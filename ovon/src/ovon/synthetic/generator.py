from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np

@dataclass
class CandidateSite:
    site_id: int
    x: float  # km relative to origin
    y: float  # km relative to origin
    habitat: np.ndarray  # composition vector (e.g., [forest, wetland, urban])
    is_public: bool = True
    is_safe: bool = True
    observation_minutes: int = 10
    true_p: np.ndarray = field(default_factory=lambda: np.array([]))  # shape (n_species,)
    bootstrap_predictions: np.ndarray = field(default_factory=lambda: np.array([[]]))  # shape (n_species, n_bootstrap)
    park_name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

@dataclass
class ExistingObservation:
    x_km: float
    y_km: float
    habitat: np.ndarray
    week: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    observer_id: Optional[str] = None

@dataclass
class SyntheticDataset:
    candidate_sites: List[CandidateSite]
    travel_time_matrix: np.ndarray  # shape (N, N) in minutes
    existing_observations: List[Union[Tuple[float, float, np.ndarray, int], ExistingObservation]]  # (x, y, habitat, week) or ExistingObservation
    n_species: int
    n_bootstrap: int
    species_names: List[str]

def generate_synthetic_dataset(
    n_sites: int = 40,
    n_species: int = 8,
    n_bootstrap: int = 30,
    n_existing: int = 50,
    area_size_km: float = 40.0,
    avg_speed_kmh: float = 40.0,
    seed: int = 42
) -> SyntheticDataset:
    """
    Generate a reproducible synthetic landscape with candidate sites,
    habitat features, bootstrap predictions, and travel times.
    """
    rng = np.random.default_rng(seed)

    # 1. Generate site coordinates
    coords = rng.uniform(-area_size_km / 2.0, area_size_km / 2.0, size=(n_sites, 2))

    # 2. Generate Dirichlet habitat compositions (3 classes: forest, wetland, urban)
    habitat_alpha = [1.5, 1.0, 1.2]
    habitats = rng.dirichlet(habitat_alpha, size=n_sites)

    # 3. Species names
    species_names = [f"Species_{i+1}" for i in range(n_species)]

    # 4. Generate true encounter probability function coefficients
    # Each species prefers a different linear combination of habitats + spatial gradient
    species_coeffs = rng.normal(0, 1.5, size=(n_species, 3))
    
    candidate_sites: List[CandidateSite] = []
    for i in range(n_sites):
        # Compute true encounter probabilities for each species
        logits = np.dot(species_coeffs, habitats[i]) + 0.05 * coords[i, 0]
        true_p = 1.0 / (1.0 + np.exp(-logits))
        true_p = np.clip(true_p, 0.05, 0.95)

        # Generate ensemble bootstrap predictions centered around true_p with variance
        # High variance for under-sampled habitats/spatial edges
        uncertainty_scale = 0.15 + 0.1 * np.abs(coords[i, 0]) / area_size_km
        bootstrap_preds = np.zeros((n_species, n_bootstrap))
        for s in range(n_species):
            # Beta distribution around true_p
            p_mean = true_p[s]
            conc = max(2.0, (1.0 - uncertainty_scale) * 20.0)
            a = max(0.1, p_mean * conc)
            b_param = max(0.1, (1.0 - p_mean) * conc)
            bootstrap_preds[s] = rng.beta(a, b_param, size=n_bootstrap)

        # 5% of sites might be private/restricted
        is_public = bool(rng.random() > 0.05)
        # 2% might have safety restrictions
        is_safe = bool(rng.random() > 0.02)

        site = CandidateSite(
            site_id=i,
            x=coords[i, 0],
            y=coords[i, 1],
            habitat=habitats[i],
            is_public=is_public,
            is_safe=is_safe,
            observation_minutes=10,
            true_p=true_p,
            bootstrap_predictions=bootstrap_preds
        )
        candidate_sites.append(site)

    # 5. Travel time matrix (Euclidean distance / speed * 60 minutes)
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]  # (N, N, 2)
    dist_km = np.sqrt(np.sum(diff ** 2, axis=-1))
    travel_time_min = (dist_km / avg_speed_kmh) * 60.0

    # 6. Generate existing baseline observations (e.g. past checklists)
    existing_coords = rng.uniform(-area_size_km / 2.0, area_size_km / 2.0, size=(n_existing, 2))
    existing_habitats = rng.dirichlet(habitat_alpha, size=n_existing)
    existing_obs = [
        (existing_coords[k, 0], existing_coords[k, 1], existing_habitats[k], int(rng.integers(1, 52)))
        for k in range(n_existing)
    ]

    return SyntheticDataset(
        candidate_sites=candidate_sites,
        travel_time_matrix=travel_time_min,
        existing_observations=existing_obs,
        n_species=n_species,
        n_bootstrap=n_bootstrap,
        species_names=species_names
    )
