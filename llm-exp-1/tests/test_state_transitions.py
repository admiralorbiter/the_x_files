"""
Unit Tests for IMPACT State-Transition & Statistical Analysis Module.
"""

import math
import numpy as np
import pandas as pd
import pytest

from src.impact.analysis.transitions import (
    classify_state,
    verify_algebraic_identity,
    compute_wilson_ci,
    compute_destabilization_metrics,
    detect_missing_cells_from_manifest,
    compute_missingness_bounds,
    validate_both_order_pair,
)


def test_state_classification():
    """Verify exact 4-state mapping: (0,0)->R, (0,1)->C, (1,1)->M, (1,0)->G."""
    assert classify_state(0, 0) == "R"
    assert classify_state(0, 1) == "C"
    assert classify_state(1, 1) == "M"
    assert classify_state(1, 0) == "G"


def test_algebraic_identity():
    """Verify ΔA - ΔJ == ΔC - ΔG identity check."""
    # Test valid case
    delta_a = 0.3359
    delta_j = 0.0234
    delta_c = 0.3125
    delta_g = 0.0000
    assert verify_algebraic_identity(delta_a, delta_j, delta_c, delta_g)

    # Test invalid case
    assert not verify_algebraic_identity(0.5000, 0.1000, 0.2000, 0.0000)


def test_wilson_ci():
    """Verify Wilson score CI behavior for zero, full, and partial proportions."""
    # Zero switches (n=0) -> (NaN, NaN)
    low, high = compute_wilson_ci(0, 0)
    assert math.isnan(low) and math.isnan(high)

    # 0/9 -> [0.0, ~0.299]
    low_0, high_0 = compute_wilson_ci(0, 9)
    assert low_0 == 0.0
    assert pytest.approx(high_0, abs=0.01) == 0.299

    # 3/3 -> [~0.438, 1.0]
    low_3, high_3 = compute_wilson_ci(3, 3)
    assert pytest.approx(low_3, abs=0.01) == 0.438
    assert high_3 == 1.0


def test_both_order_requires_false_and_true():
    """Ensure duplicate False, False is not accepted as a valid order pair."""
    # Valid pair: {False, True}
    valid_df = pd.DataFrame([
        {"choice_order_reversed": False, "state_c": "R", "state_p": "C"},
        {"choice_order_reversed": True, "state_c": "R", "state_p": "C"},
    ])
    assert validate_both_order_pair(valid_df) == "robust_R_C"

    # Duplicate orders: {False, False}
    dup_df = pd.DataFrame([
        {"choice_order_reversed": False, "state_c": "R", "state_p": "C"},
        {"choice_order_reversed": False, "state_c": "R", "state_p": "C"},
    ])
    assert validate_both_order_pair(dup_df) == "invalid_duplicate_order"


def test_missing_cells_from_manifest():
    """Verify manifest missingness detection when some cell_ids are absent from observed results."""
    manifest_df = pd.DataFrame({
        "cell_id": [f"cell_{i}" for i in range(1, 9)],
        "model_id": ["m1"] * 8,
        "treatment_id": ["t1"] * 8,
    })
    observed_df = pd.DataFrame({
        "cell_id": [f"cell_{i}" for i in range(1, 8)], # Cell 8 missing
        "model_id": ["m1"] * 7,
        "treatment_id": ["t1"] * 7,
    })

    missing = detect_missing_cells_from_manifest(manifest_df, observed_df)
    assert len(missing) == 1
    assert missing.iloc[0]["cell_id"] == "cell_8"


def test_destabilization_directionality():
    """Verify rho=1 for pure targetward changes and rho=0 for equal targetward/away churn."""
    # 4 targetward, 0 away -> rho = +1.0, p_value = 0.125
    pure_targetward = pd.DataFrame({
        "is_target_action_c": [0, 0, 0, 0],
        "is_target_action_p": [1, 1, 1, 1],
    })
    metrics_pure = compute_destabilization_metrics(pure_targetward)
    assert metrics_pure["n_changed"] == 4
    assert metrics_pure["n_targetward"] == 4
    assert metrics_pure["n_away"] == 0
    assert pytest.approx(metrics_pure["directionality_ratio"]) == 1.0
    assert pytest.approx(metrics_pure["p_targetward_given_changed"]) == 1.0

    # 3 targetward, 3 away -> rho = 0.0, p_value = 1.0
    equal_churn = pd.DataFrame({
        "is_target_action_c": [0, 0, 0, 1, 1, 1],
        "is_target_action_p": [1, 1, 1, 0, 0, 0],
    })
    metrics_churn = compute_destabilization_metrics(equal_churn)
    assert metrics_churn["n_changed"] == 6
    assert metrics_churn["n_targetward"] == 3
    assert metrics_churn["n_away"] == 3
    assert pytest.approx(metrics_churn["directionality_ratio"]) == 0.0
    assert pytest.approx(metrics_churn["p_targetward_given_changed"]) == 0.5
    assert pytest.approx(metrics_churn["binomial_pvalue"]) == 1.0
