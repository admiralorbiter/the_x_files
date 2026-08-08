import numpy as np
from typing import List, Dict, Any, Optional, Callable
from ovon.utility.metrics import StandardScaler
from ovon.features.schema import EnvironmentalFeatureVector

def extract_record_habitat(
    record: Any,
    background_candidates: Optional[List[Any]] = None,
    feature_extractor: Optional[Callable[[float, float], np.ndarray]] = None
) -> np.ndarray:
    """
    Extract habitat vector for an occurrence record or candidate site.
    Uses explicit habitat/env_feature_vector if present, or feature_extractor / nearest candidate site lookup for (lat, lon).
    """
    if isinstance(record, EnvironmentalFeatureVector):
        return record.values

    hab = record.get("habitat") if isinstance(record, dict) else getattr(record, "habitat", None)
    if hab is not None:
        if isinstance(hab, EnvironmentalFeatureVector):
            return hab.values
        return np.asarray(hab, dtype=float)

    env_vec = record.get("env_feature_vector") if isinstance(record, dict) else getattr(record, "env_feature_vector", None)
    if env_vec is not None:
        if isinstance(env_vec, EnvironmentalFeatureVector):
            return env_vec.values
        return np.asarray(env_vec, dtype=float)

    lat = record.get("lat") if isinstance(record, dict) else getattr(record, "lat", None)
    lon = record.get("lon") if isinstance(record, dict) else getattr(record, "lon", None)

    if lat is not None and lon is not None:
        if feature_extractor is not None:
            extracted = feature_extractor(float(lat), float(lon))
            if extracted is not None:
                return np.asarray(extracted, dtype=float)

        if background_candidates:
            best_dist = float("inf")
            best_hab = None
            for s in background_candidates:
                s_lat = getattr(s, "lat", None)
                s_lon = getattr(s, "lon", None)
                if s_lat is not None and s_lon is not None:
                    d_sq = (s_lat - float(lat))**2 + (s_lon - float(lon))**2
                else:
                    d_sq = (getattr(s, "x", 0.0)**2) + (getattr(s, "y", 0.0)**2)
                if d_sq < best_dist:
                    best_dist = d_sq
                    best_hab = getattr(s, "habitat", None)
            if best_hab is not None:
                return np.asarray(best_hab, dtype=float)

    if isinstance(record, dict) and "tree_canopy_pct" in record:
        return np.array([
            float(record.get("tree_canopy_pct", 0.40)),
            float(record.get("impervious_surface_pct", 0.30)),
            float(record.get("distance_to_water_km", 0.50)),
            float(record.get("greenness_index", 0.60))
        ])

    if background_candidates and len(background_candidates) > 0:
        first_hab = getattr(background_candidates[0], "habitat", None)
        if first_hab is not None:
            return np.asarray(first_hab, dtype=float)

    return np.array([0.40, 0.30, 0.50, 0.60])

class HabitatAnalogSearch:
    """
    Learns environmental habitat signatures from verified species presence records
    and predicts environmental analog scores A(s, i) in [0, 1] for unvisited candidate sites.
    Fits feature scaler on regional background dataset candidates first to ensure metric stability.
    Enforces matching feature vector dimensions across candidates and evidence.
    """

    def __init__(self, length_habitat: float = 1.0):
        self.length_habitat = length_habitat
        self.scaler = StandardScaler()
        self.mean_vector: Optional[np.ndarray] = None
        self.presence_vectors_std: Optional[np.ndarray] = None
        self.species_id: Optional[str] = None
        self.expected_dim: Optional[int] = None

    def fit(
        self,
        species_id: str,
        occurrence_records: List[Any],
        background_candidates: Optional[List[Any]] = None,
        feature_extractor: Optional[Callable[[float, float], np.ndarray]] = None
    ):
        """Fit habitat signature from species occurrence points using regional background scaling."""
        self.species_id = species_id

        # 1. Determine feature schema dimension from background candidates first
        if background_candidates:
            bg_features = []
            for s in background_candidates:
                h = extract_record_habitat(s)
                bg_features.append(h)

            if bg_features:
                self.expected_dim = len(bg_features[0])
                for idx, h in enumerate(bg_features):
                    if len(h) != self.expected_dim:
                        raise ValueError(
                            f"Background candidate site {idx} feature dimension {len(h)} "
                            f"does not match expected dimension {self.expected_dim}."
                        )
                self.scaler.fit(np.array(bg_features))

        # 2. Extract species presence vectors from occurrence records
        features = []
        for r in occurrence_records:
            hab = extract_record_habitat(r, background_candidates=background_candidates, feature_extractor=feature_extractor)
            if self.expected_dim is not None and len(hab) != self.expected_dim:
                raise ValueError(
                    f"Occurrence record feature dimension ({len(hab)}) does not match expected schema dimension ({self.expected_dim})."
                )
            features.append(hab)

        if not features:
            fallback_dim = self.expected_dim or 4
            features = [np.full(fallback_dim, 0.40)]

        if self.expected_dim is None:
            self.expected_dim = len(features[0])

        X = np.array(features)
        if self.scaler.mean is None:
            self.scaler.fit(X)

        X_std = self.scaler.transform(X)
        self.mean_vector = np.mean(X_std, axis=0)
        self.presence_vectors_std = X_std

    def predict_habitat_match(self, candidate_sites: List[Any]) -> np.ndarray:
        """
        Compute Gaussian kernel habitat analog similarity A(s, i) for candidate sites.
        Validates feature vector dimensions strictly.
        """
        if self.mean_vector is None or not candidate_sites:
            return np.full(len(candidate_sites), 0.5)

        target_dim = self.expected_dim or len(self.mean_vector)
        scores = []
        for s in candidate_sites:
            hab = extract_record_habitat(s)
            if len(hab) != target_dim:
                raise ValueError(
                    f"Candidate site feature dimension ({len(hab)}) does not match model expected dimension ({target_dim})."
                )

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
    Demonstration Richness-Debt Heuristic: Debt_i = E[species_richness_i] - observed_richness_i.
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

        expected_richness = int(round(4 + (canopy * 12) + (greenness * 8)))
        observed_richness = getattr(s, "n_observed_species", min(3, expected_richness - 4))
        debt = max(0, expected_richness - observed_richness)

        results.append({
            "site_id": s.site_id,
            "site_name": park_name,
            "expected_richness": expected_richness,
            "observed_richness": observed_richness,
            "richness_debt": debt,
            "explanation": f"{park_name}: Expected {expected_richness} species based on canopy & greenness, but only {observed_richness} observed (Demonstration Richness Debt: {debt})."
        })

    return results
