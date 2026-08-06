import numpy as np
from typing import List, Dict, Any, Optional
from ovon.utility.metrics import StandardScaler, standardize_features

class HabitatAnalogSearch:
    """
    Learns environmental habitat signatures from verified species presence records
    and predicts environmental analog scores A(s, i) in [0, 1] for unvisited candidate sites.
    """

    def __init__(self, length_habitat: float = 1.0):
        self.length_habitat = length_habitat
        self.scaler = StandardScaler()
        self.mean_vector: Optional[np.ndarray] = None
        self.presence_vectors_std: Optional[np.ndarray] = None
        self.species_id: Optional[str] = None

    def fit(self, species_id: str, occurrence_records: List[Dict[str, Any]]):
        """Fit habitat signature from species occurrence points."""
        self.species_id = species_id
        features = []

        for r in occurrence_records:
            hab = r.get("habitat")
            if hab is None:
                # Construct feature vector from named covariates if present
                hab = np.array([
                    r.get("tree_canopy_pct", 0.40),
                    r.get("impervious_surface_pct", 0.30),
                    r.get("distance_to_water_km", 0.50),
                    r.get("greenness_index", 0.60)
                ])
            features.append(np.asarray(hab, dtype=float))

        if not features:
            # Default forest edge habitat signature
            features = [np.array([0.45, 0.25, 0.30, 0.65])]

        X = np.array(features)
        self.scaler.fit(X)
        X_std = self.scaler.transform(X)
        self.mean_vector = np.mean(X_std, axis=0)
        self.presence_vectors_std = X_std

    def predict_habitat_match(self, candidate_sites: List[Any]) -> np.ndarray:
        """
        Compute Gaussian kernel habitat analog similarity A(s, i) for candidate sites.
        """
        if self.mean_vector is None or not candidate_sites:
            return np.full(len(candidate_sites), 0.5)

        target_dim = len(self.mean_vector)
        scores = []
        for s in candidate_sites:
            hab = np.asarray(getattr(s, "habitat", np.array([0.40, 0.30, 0.50, 0.60])), dtype=float)
            if len(hab) < target_dim:
                hab = np.pad(hab, (0, target_dim - len(hab)), mode='constant', constant_values=0.5)
            elif len(hab) > target_dim:
                hab = hab[:target_dim]

            h_std = self.scaler.transform(np.array([hab]))[0]

            if self.presence_vectors_std is not None and len(self.presence_vectors_std) > 1:
                d_sqs = np.sum((self.presence_vectors_std - h_std)**2, axis=1)
                k_val = np.mean(np.exp(-d_sqs / (2.0 * self.length_habitat**2)))
            else:
                d_sq = np.sum((h_std - self.mean_vector)**2)
                k_val = np.exp(-d_sq / (2.0 * self.length_habitat**2))

            scores.append(float(k_val))

        return np.clip(np.array(scores), 0.001, 0.999)

def calculate_expected_richness_debt(
    candidate_sites: List[Any],
    gbif_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calculate Expected Richness Debt: Debt_i = E[species_richness_i] - observed_richness_i.
    Identifies under-sampled urban greenways missing expected regional species.
    """
    unique_species = list(set([r.get("species") for r in gbif_records if r.get("species")]))
    n_regional_species = max(5, len(unique_species))

    results = []
    for s in candidate_sites:
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        covs = getattr(s, "env_covariates", None)
        canopy = covs.tree_canopy_pct if covs else 0.40
        greenness = covs.greenness_index if covs else 0.60

        # E[richness] modeled from canopy and greenness index
        expected_richness = int(round(4 + (canopy * 12) + (greenness * 8)))
        observed_richness = getattr(s, "n_observed_species", min(3, expected_richness - 4))
        debt = max(0, expected_richness - observed_richness)

        results.append({
            "site_id": s.site_id,
            "site_name": park_name,
            "expected_richness": expected_richness,
            "observed_richness": observed_richness,
            "richness_debt": debt,
            "explanation": f"{park_name}: Expected {expected_richness} species based on canopy & greenness, but only {observed_richness} observed (Richness Debt: {debt})."
        })

    return results
