import pytest
import numpy as np

from ovon.models.encounter import (
    CalibratedTreeEncounterModel,
    SpatialBlockCV,
    BootstrapEnsembleUncertainty,
    extract_feature_vector
)

def test_calibrated_tree_model():
    rng = np.random.default_rng(42)
    X = rng.normal(0, 1, size=(50, 7))
    y = rng.binomial(1, 0.4, size=50)

    model = CalibratedTreeEncounterModel(species_name="Indigo Bunting")
    model.fit(X, y)

    preds = model.predict_encounter_rate(X[:5])
    assert len(preds) == 5
    assert (preds >= 0.0).all() and (preds <= 1.0).all()

    metrics = model.evaluate(X[30:], y[30:])
    assert metrics.brier_score >= 0.0
    assert metrics.auc_roc >= 0.0

def test_spatial_block_cv():
    rng = np.random.default_rng(42)
    coords = rng.uniform(38.5, 39.5, size=(40, 2))

    sb_cv = SpatialBlockCV(n_blocks=4)
    splits = sb_cv.split(coords)

    assert len(splits) >= 2
    for train_idx, val_idx in splits:
        assert len(train_idx) > 0
        assert len(val_idx) > 0
        # Assert no overlap
        assert len(set(train_idx).intersection(set(val_idx))) == 0

def test_bootstrap_ensemble_uncertainty():
    rng = np.random.default_rng(42)
    X = rng.normal(0, 1, size=(40, 7))
    y = rng.binomial(1, 0.5, size=40)

    engine = BootstrapEnsembleUncertainty(n_bootstrap=10, seed=42)
    ensemble = engine.fit_ensemble("Bald Eagle", X, y)

    assert len(ensemble) == 10

    means, qbc_scores = engine.predict_ensemble(ensemble, X[:5])
    assert len(means) == 5
    assert len(qbc_scores) == 5
    assert (qbc_scores >= 0.0).all()
