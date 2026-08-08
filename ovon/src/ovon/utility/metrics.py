import numpy as np
from typing import List, Tuple, Optional, Any, Dict
from ovon.synthetic.generator import CandidateSite

# List of known seasonal migratory bird keywords vs year-round residents
MIGRATORY_KEYWORDS = [
    "warbler", "bunting", "sapsucker", "kingfisher", "eagle", "falcon",
    "flycatcher", "tanager", "vireo", "thrush", "oriole", "swallow", "duck", "teal", "heron"
]

class StandardScaler:
    """Dynamic Z-score feature standardization fitted on training data."""
    def __init__(self):
        self.mean: Optional[np.ndarray] = None
        self.scale: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray):
        X = np.asarray(X, dtype=float)
        self.mean = np.mean(X, axis=0)
        self.scale = np.std(X, axis=0)
        self.scale = np.where(self.scale == 0, 1.0, self.scale)

    def transform(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        if self.mean is None or self.scale is None:
            return X
        return (X - self.mean) / self.scale

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

def bernoulli_entropy(p: np.ndarray) -> np.ndarray:
    """Calculate binary Bernoulli entropy H(p) = -p log2(p) - (1-p) log2(1-p)."""
    p = np.clip(p, 1e-12, 1.0 - 1e-12)
    return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)

def duration_efficiency_multiplier(duration_minutes: float) -> float:
    """Compute diminishing return duration efficiency multiplier M(tau) = 1 - exp(-0.12 * tau)."""
    return float(1.0 - np.exp(-0.12 * float(duration_minutes)))

def calculate_qbc_disagreement(bootstrap_preds: np.ndarray) -> np.ndarray:
    """Calculate Query-by-Committee disagreement for species predictions."""
    mean_preds = np.mean(bootstrap_preds, axis=1)
    entropy_of_mean = bernoulli_entropy(mean_preds)
    mean_of_entropy = np.mean(bernoulli_entropy(bootstrap_preds), axis=1)
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

def standardize_features(hab: np.ndarray, means: Optional[np.ndarray] = None, stds: Optional[np.ndarray] = None) -> np.ndarray:
    """Standardize feature vector: z_j = (x_j - mu_j) / sigma_j."""
    hab = np.asarray(hab, dtype=float)
    if means is None:
        means = np.full(len(hab), 0.40)
    if stds is None:
        stds = np.full(len(hab), 0.20)
    stds = np.maximum(stds, 1e-4)
    return (hab - means) / stds

def spatial_habitat_kernel(
    x1: float, y1: float, hab1: np.ndarray,
    x2: float, y2: float, hab2: np.ndarray,
    week1: Optional[int] = None,
    week2: Optional[int] = None,
    spatial_length_km: float = 10.0,
    length_habitat: float = 1.0,
    length_time_weeks: float = 4.0,
    length_spatial: Optional[float] = None,
    means: Optional[np.ndarray] = None,
    stds: Optional[np.ndarray] = None
) -> float:
    """
    Compute pairwise Gaussian similarity kernel across space (km), standardized habitat, and cyclical annual week.
    Raises ValueError on dimension mismatch.
    """
    if length_spatial is not None:
        spatial_length_km = length_spatial

    d_space_sq = (x1 - x2)**2 + (y1 - y2)**2
    
    h1 = np.asarray(hab1, dtype=float)
    h2 = np.asarray(hab2, dtype=float)
    if len(h1) != len(h2):
        raise ValueError(f"Habitat feature vector dimension mismatch: len(h1)={len(h1)} vs len(h2)={len(h2)}.")

    h1_std = standardize_features(h1, means=means, stds=stds)
    h2_std = standardize_features(h2, means=means, stds=stds)

    d_hab_sq = float(np.sum((h1_std - h2_std)**2))

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
    length_habitat: float = 1.0,
    length_time_weeks: float = 4.0,
    length_spatial: Optional[float] = None
) -> float:
    """Calculate normalized spatiotemporal redundancy index R(site | D, week) in [0, 1)."""
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

        k_val = spatial_habitat_kernel(
            site.x, site.y, site.habitat,
            obs_x, obs_y, obs_hab,
            week1=survey_week, week2=obs_week,
            spatial_length_km=spatial_length_km,
            length_habitat=length_habitat,
            length_time_weeks=length_time_weeks
        )
        total_coverage += k_val

    return float(total_coverage / (1.0 + total_coverage))

def compute_set_utility(
    sites: List[CandidateSite],
    existing_observations: List[Any],
    species_names: Optional[List[str]] = None,
    lambda_redundancy: float = 0.5,
    survey_week: int = 18,
    opportunity_surface: Optional[Dict[int, float]] = None,
    reward_protocol: Optional[Any] = None,
    length_spatial: float = 2.0
) -> float:
    """
    Compute overall route utility combining epistemic info gain, duration efficiency,
    and spatial/temporal redundancy penalty. Accepts dynamic reward_protocol or static opportunity_surface.
    """
    if not sites:
        return 0.0

    from ovon.data.phenology import get_weekly_species_weights
    
    weights = get_weekly_species_weights(species_names, survey_week)

    weighted_qbc = []
    for s in sites:
        if reward_protocol is not None and hasattr(reward_protocol, "reward"):
            dur = float(getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 10)))
            w_qbc = float(reward_protocol.reward(s, dur))
        else:
            qbc_scores = getattr(s, "qbc_scores", None)
            if qbc_scores is not None and len(qbc_scores) > 0:
                qbc = qbc_scores
            elif getattr(s, "bootstrap_predictions", None) is not None and getattr(s, "bootstrap_predictions").size > 0:
                qbc = calculate_qbc_disagreement(s.bootstrap_predictions)
            else:
                qbc = np.zeros(len(weights))

            min_len = min(len(weights), len(qbc))
            w_qbc = float(np.sum(np.array(weights)[:min_len] * np.array(qbc)[:min_len]))

            if opportunity_surface is not None and s.site_id in opportunity_surface:
                w_qbc = w_qbc * opportunity_surface[s.site_id]

        weighted_qbc.append(w_qbc)

    total_info = 0.0
    for idx, s in enumerate(sites):
        R_hist = calculate_site_redundancy_to_history(
            s, existing_observations, survey_week=survey_week, spatial_length_km=length_spatial
        )
        if reward_protocol is not None and hasattr(reward_protocol, "reward"):
            total_info += weighted_qbc[idx] * (1.0 - R_hist)
        else:
            dur = float(getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 10)))
            dur_efficiency = duration_efficiency_multiplier(dur)
            total_info += weighted_qbc[idx] * (1.0 - R_hist) * dur_efficiency

    n_sites = len(sites)
    if n_sites <= 1:
        route_redundancy = 0.0
    else:
        pair_redundancies = []
        for i in range(n_sites):
            for j in range(i + 1, n_sites):
                k_val = spatial_habitat_kernel(
                    sites[i].x, sites[i].y, sites[i].habitat,
                    sites[j].x, sites[j].y, sites[j].habitat,
                    week1=survey_week, week2=survey_week,
                    spatial_length_km=length_spatial
                )
                pair_redundancies.append(k_val)
        route_redundancy = float(np.mean(pair_redundancies)) if pair_redundancies else 0.0

    return float(total_info - (lambda_redundancy * route_redundancy))
