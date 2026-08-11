"""
Core State-Transition & Statistical Analysis Module for IMPACT.
Contains pure calculation functions for response-state classification,
transition matrices, two-stage susceptibility/assimilation modeling,
destabilization metrics, and manifest missingness bounds.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Tuple, Any, List, Optional


def classify_state(is_target_judgment: int, is_target_action: int) -> str:
    """
    Classify a single response relative to institutional target T:
    - R (Resistance): J=0, A=0 (J!=T, A!=T)
    - C (Compartmentalized Compliance): J=0, A=1 (J!=T, A=T)
    - M (Normative Assimilation): J=1, A=1 (J=T, A=T)
    - G (Judgment-Only Alignment): J=1, A=0 (J=T, A!=T)
    """
    if is_target_judgment == 0 and is_target_action == 0:
        return "R"
    elif is_target_judgment == 0 and is_target_action == 1:
        return "C"
    elif is_target_judgment == 1 and is_target_action == 1:
        return "M"
    elif is_target_judgment == 1 and is_target_action == 0:
        return "G"
    return "UNKNOWN"


def verify_algebraic_identity(delta_a: float, delta_j: float, delta_c: float, delta_g: float, atol: float = 1e-4) -> bool:
    """
    Verifies the mathematical identity: ΔA - ΔJ = ΔC - ΔG
    """
    left = delta_a - delta_j
    right = delta_c - delta_g
    return bool(np.isclose(left, right, atol=atol))


def compute_wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Computes Wilson score interval for binomial proportion k/n.
    Returns (lower, upper). Returns (NaN, NaN) if n == 0.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p_hat = k / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, float(centre - margin)), min(1.0, float(centre + margin)))


def compute_destabilization_metrics(df_pairs: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes gross vs net decision destabilization metrics from paired (control, pressure) observations.
    """
    n_matched = len(df_pairs)
    if n_matched == 0:
        return {
            "n_matched": 0, "n_changed": 0, "n_targetward": 0, "n_away": 0,
            "gross_change_rate": 0.0, "net_shift": 0.0, "directionality_ratio": 0.0,
            "p_targetward_given_changed": float("nan"), "binomial_pvalue": float("nan")
        }

    changed = df_pairs[df_pairs["is_target_action_p"] != df_pairs["is_target_action_c"]]
    n_changed = len(changed)

    n_targetward = int(((changed["is_target_action_c"] == 0) & (changed["is_target_action_p"] == 1)).sum())
    n_away = int(((changed["is_target_action_c"] == 1) & (changed["is_target_action_p"] == 0)).sum())

    net_shift = float(df_pairs["is_target_action_p"].mean() - df_pairs["is_target_action_c"].mean())
    gross_rate = float(n_changed / n_matched)

    if n_changed > 0:
        rho = float(net_shift / gross_rate)
        p_targetward = float(n_targetward / n_changed)
        # Exact binomial test against H0: p = 0.5
        binom_res = stats.binomtest(n_targetward, n_changed, p=0.5)
        p_value = float(binom_res.pvalue)
    else:
        rho = 0.0
        p_targetward = float("nan")
        p_value = float("nan")

    return {
        "n_matched": n_matched,
        "n_changed": n_changed,
        "n_targetward": n_targetward,
        "n_away": n_away,
        "gross_change_rate": gross_rate,
        "net_shift": net_shift,
        "directionality_ratio": rho,
        "p_targetward_given_changed": p_targetward,
        "binomial_pvalue": p_value
    }


def detect_missing_cells_from_manifest(manifest_df: pd.DataFrame, observed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies terminal missing cells by comparing scenario_manifest.csv against observed direct-valid results.
    """
    observed_ids = set(observed_df["cell_id"])
    missing_df = manifest_df[~manifest_df["cell_id"].isin(observed_ids)].copy()
    return missing_df


def compute_missingness_bounds(
    df_primary: pd.DataFrame,
    missing_df: pd.DataFrame,
    model_id: str,
    treatment_id: str,
    control_id: str
) -> Dict[str, Any]:
    """
    Computes lower and upper sensitivity bounds for treatment action delta (ΔA)
    under extreme missing-data assumptions (all missing = 0 vs all missing = 1).
    """
    m_obs = df_primary[(df_primary["model_id"] == model_id) & (df_primary["treatment_id"] == treatment_id)]
    c_obs = df_primary[(df_primary["model_id"] == model_id) & (df_primary["treatment_id"] == control_id)]
    
    n_obs = len(m_obs)
    m_missing = missing_df[(missing_df["model_id"] == model_id) & (missing_df["treatment_id"] == treatment_id)]
    n_miss = len(m_missing)
    
    if n_obs == 0:
        return {"n_observed": 0, "n_missing": n_miss, "delta_observed": 0.0, "delta_lower_bound": 0.0, "delta_upper_bound": 0.0}

    c_mean = float(c_obs["is_target_action"].mean())
    obs_target_sum = int(m_obs["is_target_action"].sum())
    
    # Observed delta
    delta_obs = float(m_obs["is_target_action"].mean() - c_mean)
    
    # Lower bound: assume ALL missing pressure cells choose 0 (A_p = 0)
    lower_p_rate = obs_target_sum / (n_obs + n_miss)
    delta_lower = float(lower_p_rate - c_mean)
    
    # Upper bound: assume ALL missing pressure cells choose 1 (A_p = 1)
    upper_p_rate = (obs_target_sum + n_miss) / (n_obs + n_miss)
    delta_upper = float(upper_p_rate - c_mean)
    
    return {
        "model_id": model_id,
        "treatment_id": treatment_id,
        "n_observed": n_obs,
        "n_missing": n_miss,
        "delta_observed": delta_obs,
        "delta_lower_bound": delta_lower,
        "delta_upper_bound": delta_upper
    }


def validate_both_order_pair(group: pd.DataFrame) -> str:
    """
    Validates a two-ordering scenario group:
    Ensures group has exactly 2 rows with distinct choice_order_reversed values ({False, True}).
    """
    if len(group) != 2:
        return "incomplete"
    orders = set(group["choice_order_reversed"])
    if orders != {False, True}:
        return "invalid_duplicate_order"
        
    c_states = group["state_c"].tolist()
    p_states = group["state_p"].tolist()
    
    if c_states == ["R", "R"]:
        if p_states == ["C", "C"]:
            return "robust_R_C"
        elif p_states == ["R", "R"]:
            return "robust_R_R"
        elif p_states == ["M", "M"]:
            return "robust_R_M"
        else:
            return "order_sensitive"
            
    return "not_both_R_control"
