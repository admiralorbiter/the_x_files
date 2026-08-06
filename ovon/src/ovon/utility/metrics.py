import numpy as np
from typing import List, Tuple, Optional, Any
from ovon.synthetic.generator import CandidateSite

# List of known seasonal migratory bird keywords vs year-round residents
MIGRATORY_KEYWORDS = [
    "warbler", "bunting", "sapsucker", "kingfisher", "eagle", "falcon",
    "flycatcher", "tanager", "vireo", "thrush", "oriole", "swallow", "duck", "teal", "heron"
]

def bernoulli_entropy(p: np.ndarray) -> np.ndarray:
    """
    Calculate binary Bernoulli entropy H(p) = -p log2(p) - (1-p) log2(1-p).
    Handles boundary cases p=0 and p=1 cleanly.
    """
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)

def calculate_qbc_disagreement(bootstrap_preds: np.ndarray) -> np.ndarray:
    """
    Calculate Query-by-Committee disagreement for species predictions.
    
    Parameters:
    -----------
    bootstrap_preds: np.ndarray of shape (n_species, n_bootstrap)

    Returns:
    --------
    disagreement: np.ndarray of shape (n_species,)
    """
    mean_preds = np.mean(bootstrap_preds, axis=1)  # (n_species,)
    entropy_of_mean = bernoulli_entropy(mean_preds)  # (n_species,)
    
    mean_of_entropy = np.mean(bernoulli_entropy(bootstrap_preds), axis=1)  # (n_species,)
    
    qbc = entropy_of_mean - mean_of_entropy
    return np.maximum(0.0, qbc)

def temporal_cyclic_distance(week1: int, week2: int) -> float:
    """Calculate cyclic annual week distance in [0, 26] weeks."""
    diff = abs(int(week1) - int(week2))
    return float(min(diff, 52 - diff))

def temporal_kernel(week1: int, week2: int, length_time_weeks: float = 4.0) -> float:
    """Compute Gaussian similarity decay across annual observation weeks."""
    d_time = temporal_cyclic_distance(week1, week2)
    return float(np.exp(-(d_time**2) / (2.0 * length_time_weeks**2)))

def spatial_habitat_kernel(
    x1: float, y1: float, hab1: np.ndarray,
    x2: float, y2: float, hab2: np.ndarray,
    week1: Optional[int] = None,
    week2: Optional[int] = None,
    spatial_length_km: float = 10.0,
    length_habitat: float = 0.5,
    length_time_weeks: float = 4.0,
    length_spatial: Optional[float] = None
) -> float:
    """
    Compute pairwise Gaussian similarity kernel across space (km), habitat, and cyclical annual week.
    """
    if length_spatial is not None:
        spatial_length_km = length_spatial

    d_space_sq = (x1 - x2)**2 + (y1 - y2)**2
    min_len = min(len(hab1), len(hab2))
    d_hab_sq = float(np.sum((hab1[:min_len] - hab2[:min_len])**2))

    k_space = np.exp(-d_space_sq / (2.0 * spatial_length_km**2))
    k_hab = np.exp(-d_hab_sq / (2.0 * length_habitat**2))

    k_time = 1.0
    if week1 is not None and week2 is not None:
        k_time = temporal_kernel(week1, week2, length_time_weeks=length_time_weeks)

    return float(k_space * k_hab * k_time)

def calculate_site_redundancy_to_history(
    site: CandidateSite,
    existing_observations: List[Any],
    survey_week: int = 18,
    spatial_length_km: float = 10.0,
    length_habitat: float = 0.5,
    length_time_weeks: float = 4.0,
    length_spatial: Optional[float] = None
) -> float:
    """
    Calculate normalized spatiotemporal redundancy index R(site | D, week) in [0, 1).
    """
    if not existing_observations:
        return 0.0

    if length_spatial is not None:
        spatial_length_km = length_spatial

    total_coverage = 0.0
    for obs in existing_observations:
        if isinstance(obs, (tuple, list)):
            obs_x, obs_y, obs_hab = obs[0], obs[1], obs[2]
            obs_week = obs[3] if len(obs) > 3 else 18
        else:
            obs_x = getattr(obs, "x_km", getattr(obs, "x", 0.0))
            obs_y = getattr(obs, "y_km", getattr(obs, "y", 0.0))
            obs_hab = getattr(obs, "habitat", np.array([0.25, 0.25, 0.25, 0.25]))
            obs_week = getattr(obs, "week", 18)

        k = spatial_habitat_kernel(
            site.x, site.y, site.habitat,
            obs_x, obs_y, obs_hab,
            week1=survey_week, week2=obs_week,
            spatial_length_km=spatial_length_km,
            length_habitat=length_habitat,
            length_time_weeks=length_time_weeks
        )
        total_coverage += k

    return float(total_coverage / (1.0 + total_coverage))

def get_species_migratory_weights(species_names: List[str]) -> np.ndarray:
    """
    Assign higher optimization weights to seasonal migratory species over year-round residents.
    """
    n = len(species_names)
    weights = np.ones(n)
    for i, sp in enumerate(species_names):
        sp_lower = sp.lower()
        if any(kw in sp_lower for kw in MIGRATORY_KEYWORDS):
            weights[i] = 2.5
        else:
            weights[i] = 1.0

    return weights / np.sum(weights)

def duration_efficiency_multiplier(duration_minutes: float) -> float:
    """Calculate asymptotic survey duration information multiplier M(tau) in (0, 1]."""
    tau = float(max(1.0, duration_minutes))
    return float(1.0 - np.exp(-0.12 * tau))

def compute_set_utility(
    selected_sites: List[CandidateSite],
    existing_observations: List[Any],
    species_weights: Optional[np.ndarray] = None,
    species_names: Optional[List[str]] = None,
    lambda_redundancy: float = 0.5,
    survey_week: int = 18,
    spatial_length_km: float = 10.0,
    length_habitat: float = 0.5,
    length_time_weeks: float = 4.0,
    length_spatial: Optional[float] = None
) -> float:
    """
    Compute total multi-species information utility for a set of selected sites A with variable durations.
    
    U(A) = sum_s w_s [ sum_{a in A} q(s, a) * M(tau_a) * (1 - R(a|D, week)) - lambda * sum_{a,b in A} k(a, b) ]
    """
    if not selected_sites:
        return 0.0

    if length_spatial is not None:
        spatial_length_km = length_spatial

    n_species = selected_sites[0].bootstrap_predictions.shape[0]
    if species_weights is None:
        if species_names and len(species_names) == n_species:
            from ovon.data.phenology import get_weekly_species_weights
            species_weights = get_weekly_species_weights(species_names, survey_week)
        else:
            species_weights = np.ones(n_species) / n_species

    total_utility = 0.0

    # 1. Pointwise information value adjusted by duration efficiency and historical redundancy
    for site in selected_sites:
        qbc_scores = calculate_qbc_disagreement(site.bootstrap_predictions)  # (n_species,)
        redundancy_hist = calculate_site_redundancy_to_history(
            site, existing_observations,
            survey_week=survey_week,
            spatial_length_km=spatial_length_km,
            length_habitat=length_habitat,
            length_time_weeks=length_time_weeks
        )
        tau = getattr(site, "allocated_observation_minutes", getattr(site, "observation_minutes", 5))
        duration_eff = duration_efficiency_multiplier(tau)
        site_val = np.sum(species_weights * qbc_scores) * duration_eff * (1.0 - redundancy_hist)
        total_utility += site_val

    # 2. Pairwise redundancy penalty among selected sites
    n_sel = len(selected_sites)
    pairwise_penalty = 0.0
    for i in range(n_sel):
        for j in range(i + 1, n_sel):
            s1 = selected_sites[i]
            s2 = selected_sites[j]
            k_ij = spatial_habitat_kernel(
                s1.x, s1.y, s1.habitat,
                s2.x, s2.y, s2.habitat,
                week1=survey_week, week2=survey_week,
                spatial_length_km=spatial_length_km,
                length_habitat=length_habitat,
                length_time_weeks=length_time_weeks
            )
            pairwise_penalty += k_ij

    return float(total_utility - (lambda_redundancy * pairwise_penalty))
