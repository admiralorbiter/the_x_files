import numpy as np
from typing import List, Tuple, Optional
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

def spatial_habitat_kernel(
    x1: float, y1: float, hab1: np.ndarray,
    x2: float, y2: float, hab2: np.ndarray,
    length_spatial: float = 10.0,
    length_habitat: float = 0.5
) -> float:
    """
    Compute pairwise Gaussian similarity kernel across space and habitat.
    """
    d_space_sq = (x1 - x2)**2 + (y1 - y2)**2
    d_hab_sq = np.sum((hab1 - hab2)**2)

    k_space = np.exp(-d_space_sq / (2.0 * length_spatial**2))
    k_hab = np.exp(-d_hab_sq / (2.0 * length_habitat**2))

    return float(k_space * k_hab)

def calculate_site_redundancy_to_history(
    site: CandidateSite,
    existing_observations: List[Tuple[float, float, np.ndarray, int]],
    length_spatial: float = 10.0,
    length_habitat: float = 0.5
) -> float:
    """
    Calculate normalized redundancy index R(site | D) in [0, 1).
    """
    if not existing_observations:
        return 0.0

    total_coverage = 0.0
    for obs_x, obs_y, obs_hab, _ in existing_observations:
        k = spatial_habitat_kernel(
            site.x, site.y, site.habitat,
            obs_x, obs_y, obs_hab,
            length_spatial=length_spatial,
            length_habitat=length_habitat
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
            weights[i] = 2.5  # 2.5x weight for seasonal migrants
        else:
            weights[i] = 1.0  # 1.0x weight for residents

    return weights / np.sum(weights)

def compute_set_utility(
    selected_sites: List[CandidateSite],
    existing_observations: List[Tuple[float, float, np.ndarray, int]],
    species_weights: Optional[np.ndarray] = None,
    species_names: Optional[List[str]] = None,
    lambda_redundancy: float = 0.5,
    length_spatial: float = 10.0,
    length_habitat: float = 0.5
) -> float:
    """
    Compute total multi-species information utility for a set of selected sites A.
    
    U(A) = sum_s w_s [ sum_{a in A} q(s, a) * (1 - R(a|D)) - lambda * sum_{a,b in A} k(a, b) ]
    """
    if not selected_sites:
        return 0.0

    n_species = selected_sites[0].bootstrap_predictions.shape[0]
    if species_weights is None:
        if species_names and len(species_names) == n_species:
            species_weights = get_species_migratory_weights(species_names)
        else:
            species_weights = np.ones(n_species) / n_species

    total_utility = 0.0

    # 1. Pointwise information value adjusted by historical redundancy
    for site in selected_sites:
        qbc_scores = calculate_qbc_disagreement(site.bootstrap_predictions)  # (n_species,)
        redundancy_hist = calculate_site_redundancy_to_history(
            site, existing_observations, length_spatial, length_habitat
        )
        site_val = np.sum(species_weights * qbc_scores) * (1.0 - redundancy_hist)
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
                length_spatial=length_spatial,
                length_habitat=length_habitat
            )
            pairwise_penalty += k_ij

    total_utility -= (lambda_redundancy * 0.005) * pairwise_penalty
    return float(total_utility)
