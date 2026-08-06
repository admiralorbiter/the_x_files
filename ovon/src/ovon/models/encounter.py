import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from ovon.utility.metrics import bernoulli_entropy, calculate_qbc_disagreement

@dataclass
class ModelEvaluationMetrics:
    species_name: str
    brier_score: float
    log_loss_score: float
    auc_roc: float
    n_samples: int
    n_positive: int

def extract_feature_vector(habitat: np.ndarray, week: int, duration_min: float = 10.0, distance_km: float = 0.0) -> np.ndarray:
    """
    Construct feature vector: [forest, wetland, urban, sin_week, cos_week, duration, distance]
    """
    sin_w = math.sin(2.0 * math.pi * week / 52.0)
    cos_w = math.cos(2.0 * math.pi * week / 52.0)
    return np.array([
        habitat[0], habitat[1], habitat[2],
        sin_w, cos_w,
        duration_min / 60.0, distance_km / 10.0
    ])

class ConstantPrevalenceModel:
    """Fallback model for species with insufficient class support (e.g. < 2 positive or negative samples)."""
    def __init__(self, prevalence: float):
        self.prevalence = float(np.clip(prevalence, 0.001, 0.999))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        return np.column_stack([np.full(n, 1.0 - self.prevalence), np.full(n, self.prevalence)])

class CalibratedTreeEncounterModel:
    """
    Calibrated Random Forest model for binary species encounter probability y ~ Bernoulli(pi).
    Standardizes effort to fixed stationary protocol e* (10 min, 0 km).
    """

    def __init__(self, species_name: str, n_estimators: int = 50, random_state: int = 42):
        self.species_name = species_name
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: Optional[Any] = None
        self.is_fitted = False
        self.is_constant_fallback = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit calibrated random forest model or constant prevalence fallback."""
        unique_classes, counts = np.unique(y, return_counts=True)
        if len(unique_classes) < 2 or np.min(counts) < 2:
            p_mean = float(np.mean(y)) if len(y) > 0 else 0.5
            self.model = ConstantPrevalenceModel(p_mean)
            self.is_fitted = True
            self.is_constant_fallback = True
            return

        base_rf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=6,
            random_state=self.random_state
        )
        min_class_count = int(np.min(counts))
        cv_folds = min(3, max(2, min_class_count))
        self.model = CalibratedClassifierCV(estimator=base_rf, method="sigmoid", cv=cv_folds)
        self.model.fit(X, y)
        self.is_fitted = True
        self.is_constant_fallback = False

    def predict_encounter_rate(self, X: np.ndarray) -> np.ndarray:
        """Predict calibrated encounter probabilities pi in [0.0, 1.0]."""
        if not self.is_fitted or self.model is None:
            return np.full(X.shape[0], 0.5)

        probs = self.model.predict_proba(X)
        if probs.shape[1] == 2:
            return np.clip(probs[:, 1], 0.001, 0.999)
        return np.clip(probs[:, 0], 0.001, 0.999)

    def evaluate(self, X_val: np.ndarray, y_val: np.ndarray) -> ModelEvaluationMetrics:
        """Compute evaluation metrics (Brier score, Log Loss, AUC-ROC)."""
        preds = self.predict_encounter_rate(X_val)
        brier = float(brier_score_loss(y_val, preds))
        l_loss = float(log_loss(y_val, preds))
        
        auc = 0.5
        if len(np.unique(y_val)) > 1:
            try:
                auc = float(roc_auc_score(y_val, preds))
            except Exception:
                pass

        return ModelEvaluationMetrics(
            species_name=self.species_name,
            brier_score=brier,
            log_loss_score=l_loss,
            auc_roc=auc,
            n_samples=len(y_val),
            n_positive=int(np.sum(y_val))
        )

class SpatialBlockCV:
    """
    Spatial Block Cross-Validation splitter (quadrant blocking) to prevent spatial data leakage.
    """

    def __init__(self, n_blocks: int = 4):
        self.n_blocks = n_blocks

    def split(self, coords: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Split coordinates (lat, lon) into spatial blocks.
        Returns list of (train_indices, test_indices).
        """
        median_lat = np.median(coords[:, 0])
        median_lon = np.median(coords[:, 1])

        # Define 4 spatial quadrants
        q1 = (coords[:, 0] >= median_lat) & (coords[:, 1] >= median_lon)
        q2 = (coords[:, 0] >= median_lat) & (coords[:, 1] < median_lon)
        q3 = (coords[:, 0] < median_lat) & (coords[:, 1] >= median_lon)
        q4 = (coords[:, 0] < median_lat) & (coords[:, 1] < median_lon)

        quadrants = [q1, q2, q3, q4]
        splits = []
        n_samples = len(coords)

        for q_mask in quadrants:
            test_idx = np.where(q_mask)[0]
            train_idx = np.where(~q_mask)[0]
            if len(test_idx) > 0 and len(train_idx) > 0:
                splits.append((train_idx, test_idx))

        return splits

class BootstrapEnsembleUncertainty:
    """
    Spatial-temporal block bootstrap ensemble generator fitting M models per species
    to compute ensemble mean predictions and QBC model disagreement layers.
    """

    def __init__(self, n_bootstrap: int = 20, seed: int = 42):
        self.n_bootstrap = n_bootstrap
        self.seed = seed

    def fit_ensemble(
        self,
        species_name: str,
        X: np.ndarray,
        y: np.ndarray,
        block_ids: Optional[np.ndarray] = None
    ) -> List[CalibratedTreeEncounterModel]:
        """Fit M spatial/temporal block bootstrap models by resampling blocks or observations with replacement."""
        rng = np.random.default_rng(self.seed)
        n_samples = len(X)
        ensemble = []

        if block_ids is not None:
            unique_blocks = np.unique(block_ids)
            n_blocks = len(unique_blocks)

        for m in range(self.n_bootstrap):
            if block_ids is not None and n_blocks > 1:
                sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
                bootstrap_idx = np.concatenate([np.where(block_ids == b)[0] for b in sampled_blocks])
            else:
                bootstrap_idx = rng.choice(n_samples, size=n_samples, replace=True)

            X_b = X[bootstrap_idx]
            y_b = y[bootstrap_idx]

            model = CalibratedTreeEncounterModel(
                species_name=species_name,
                n_estimators=30,
                random_state=self.seed + m
            )
            model.fit(X_b, y_b)
            ensemble.append(model)

        return ensemble

    def predict_ensemble(
        self,
        ensemble: List[CalibratedTreeEncounterModel],
        X_target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict ensemble probability matrix pi_m (shape: n_bootstrap, n_candidates)
        and compute (mean_predictions, qbc_disagreement).
        """
        n_bootstrap = len(ensemble)
        n_candidates = len(X_target)
        preds_matrix = np.zeros((n_bootstrap, n_candidates))

        for m, model in enumerate(ensemble):
            preds_matrix[m] = model.predict_encounter_rate(X_target)

        mean_preds = np.mean(preds_matrix, axis=0)  # (n_candidates,)
        
        # Calculate QBC disagreement per candidate site
        # Transpose to (1, n_bootstrap) for per-site QBC calculation
        qbc_scores = np.zeros(n_candidates)
        for i in range(n_candidates):
            site_preds = preds_matrix[:, i].reshape(1, -1)  # (1, n_bootstrap)
            qbc_scores[i] = calculate_qbc_disagreement(site_preds)[0]

        return mean_preds, qbc_scores
