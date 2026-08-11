"""
Unit Tests for IMPACT State-Transition & Statistical Analysis Module.
"""

import math
import numpy as np
import pandas as pd
import pytest

from impact.analysis.transitions import (
    classify_state,
    verify_algebraic_identity,
    compute_wilson_ci,
    compute_two_stage_summary,
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
        "cell_id": [f"cell_{i}" for i in range(1, 8)],  # Cell 8 missing
        "model_id": ["m1"] * 7,
        "treatment_id": ["t1"] * 7,
    })

    missing = detect_missing_cells_from_manifest(manifest_df, observed_df)
    assert len(missing) == 1
    assert missing.iloc[0]["cell_id"] == "cell_8"


def test_destabilization_directionality():
    """Verify rho=1 for pure targetward changes and rho=0 for equal targetward/away churn."""
    # 4 targetward, 0 away -> rho = +1.0
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

    # 3 targetward, 3 away -> rho = 0.0
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
    assert pytest.approx(metrics_churn["binomial_pvalue_descriptive"]) == 1.0


def test_two_stage_summary_asymmetric_orders():
    """
    Scenario A has headroom in both orders (2 observations).
    Scenario B has headroom in only one order (1 observation).

    The order-level point estimate should weight A twice and B once:
    p_hat = N_switch / N_R.

    Scenario A: both orders switch (is_switch=1), both assimilate (state_p=M).
    Scenario B: one order switches (is_switch=1), compartmentalizes (state_p=C).

    Expected:
    N_R = 3, N_switch = 3, susceptibility_rate = 3/3 = 1.0
    Assimilation: 2 M out of 3 switches = 2/3 ≈ 0.6667
    """
    headroom_df = pd.DataFrame({
        "scenario_id": ["A", "A", "B"],
        "state_p": ["M", "M", "C"],
        "is_switch": [1, 1, 1],
    })

    result = compute_two_stage_summary(headroom_df, n_bootstrap=500, rng=np.random.RandomState(0))

    assert result["headroom_n"] == 3
    assert result["switches_n"] == 3
    assert pytest.approx(result["susceptibility_rate"]) == 1.0
    assert result["assimilation_n"] == 2
    assert pytest.approx(result["assimilation_share"], abs=0.001) == 2 / 3


def test_two_stage_summary_zero_switches():
    """When no headroom observations switch, assimilation should be None/NaN."""
    headroom_df = pd.DataFrame({
        "scenario_id": ["A", "A", "B"],
        "state_p": ["R", "R", "R"],
        "is_switch": [0, 0, 0],
    })

    result = compute_two_stage_summary(headroom_df, n_bootstrap=100, rng=np.random.RandomState(0))

    assert result["headroom_n"] == 3
    assert result["switches_n"] == 0
    assert pytest.approx(result["susceptibility_rate"]) == 0.0
    assert result["assimilation_share"] is None
    assert result["assimilation_n"] == 0


def test_missingness_bounds_both_sides():
    """
    Verify that compute_missingness_bounds varies BOTH pressure and control missing cells.

    Setup:
    - 4 observed P1 cells: 3 target actions (sum=3, rate=0.75)
    - 2 observed C1 cells: 0 target actions (sum=0, rate=0.00)
    - 1 missing P1 cell
    - 1 missing C1 cell

    Observed delta = 0.75 - 0.00 = 0.75

    Lower bound (miss P→0, miss C→1):
      P rate = 3/(4+1) = 0.60
      C rate = (0+1)/(2+1) = 0.333
      delta_lower = 0.60 - 0.333 = 0.2667

    Upper bound (miss P→1, miss C→0):
      P rate = (3+1)/(4+1) = 0.80
      C rate = 0/(2+1) = 0.00
      delta_upper = 0.80 - 0.00 = 0.80
    """
    observed_df = pd.DataFrame({
        "model_id": ["m1"] * 6,
        "treatment_id": ["P1"] * 4 + ["C1"] * 2,
        "is_target_action": [1, 1, 1, 0, 0, 0],
    })

    missing_df = pd.DataFrame({
        "model_id": ["m1", "m1"],
        "treatment_id": ["P1", "C1"],
    })

    result = compute_missingness_bounds(observed_df, missing_df, "m1", "P1", "C1")

    assert result["n_p_observed"] == 4
    assert result["n_p_missing"] == 1
    assert result["n_c_observed"] == 2
    assert result["n_c_missing"] == 1
    assert pytest.approx(result["delta_observed"], abs=0.001) == 0.75
    assert pytest.approx(result["delta_lower_bound"], abs=0.001) == 0.2667
    assert pytest.approx(result["delta_upper_bound"], abs=0.001) == 0.80
