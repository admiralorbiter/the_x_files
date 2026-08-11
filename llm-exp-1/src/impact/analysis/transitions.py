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


def compute_two_stage_summary(
    headroom_df: pd.DataFrame,
    n_bootstrap: int = 2000,
    rng: Optional[np.random.RandomState] = None,
) -> Dict[str, Any]:
    """
    Computes two-stage susceptibility/assimilation summary from a headroom DataFrame
    (order-level matched observations where S_C = R).

    Estimand definitions:
    - Stage 1 (Susceptibility): Order-level conditional probability P(switch | S_C=R) = N_switch / N_R.
      CI: Scenario-cluster bootstrap that resamples scenario IDs and includes all eligible
      order-level observations within each sampled scenario, then recomputes the pooled rate.
    - Stage 2 (Assimilation): Order-level conditional probability P(M | switch) = N_M / N_switch.
      Descriptive Wilson score CI + scenario-cluster bootstrap CI.

    Required columns: scenario_id, state_p, is_switch (0/1).
    """
    if rng is None:
        rng = np.random.RandomState(42)

    n_r = len(headroom_df)
    if n_r == 0:
        return {
            "headroom_n": 0, "susceptibility_rate": float("nan"),
            "susceptibility_ci_lower": float("nan"), "susceptibility_ci_upper": float("nan"),
            "switches_n": 0, "assimilation_n": 0,
            "assimilation_share": None, "assimilation_wilson_ci_lower": None,
            "assimilation_wilson_ci_upper": None, "assimilation_cluster_ci_lower": None,
            "assimilation_cluster_ci_upper": None, "compliance_share": None,
        }

    n_switches = int(headroom_df["is_switch"].sum())

    # Stage 1: Order-level conditional probability with scenario-cluster bootstrap CI
    s1_rate = float(n_switches / n_r)

    # Pre-aggregate per scenario for cluster bootstrap
    scen_agg = headroom_df.groupby("scenario_id").agg(
        n_obs=("is_switch", "count"),
        n_sw=("is_switch", "sum"),
    )
    scenarios = scen_agg.index.values
    n_scen = len(scenarios)
    n_obs_arr = scen_agg["n_obs"].values.astype(float)
    n_sw_arr = scen_agg["n_sw"].values.astype(float)

    if n_scen > 1:
        boot_idx = rng.randint(0, n_scen, size=(n_bootstrap, n_scen))
        boot_sw = np.sum(n_sw_arr[boot_idx], axis=1)
        boot_obs = np.sum(n_obs_arr[boot_idx], axis=1)
        s1_boots = boot_sw / boot_obs
        s1_ci = (float(np.percentile(s1_boots, 2.5)), float(np.percentile(s1_boots, 97.5)))
    else:
        s1_ci = (s1_rate, s1_rate)

    # Stage 2: Among switchers, P(M | switch)
    if n_switches > 0:
        switches = headroom_df[headroom_df["is_switch"] == 1]
        n_assim = int((switches["state_p"] == "M").sum())
        s2_rate = float(n_assim / n_switches)
        s2_wilson_ci = compute_wilson_ci(n_assim, n_switches)

        # Scenario-cluster bootstrap for Stage 2
        scen_sw_agg = headroom_df.groupby("scenario_id").apply(
            lambda g: pd.Series({"n_sw": g["is_switch"].sum(), "n_m": (g["state_p"] == "M").sum()})
        )
        sw_scen_df = scen_sw_agg[scen_sw_agg["n_sw"] > 0]
        n_sw_scen = len(sw_scen_df)
        if n_sw_scen > 1:
            sw_arr = sw_scen_df["n_sw"].values
            m_arr = sw_scen_df["n_m"].values
            boot_idx2 = rng.randint(0, n_sw_scen, size=(n_bootstrap, n_sw_scen))
            boot_n_m = np.sum(m_arr[boot_idx2], axis=1)
            boot_n_sw = np.sum(sw_arr[boot_idx2], axis=1)
            valid = boot_n_sw > 0
            if np.any(valid):
                s2_boots = boot_n_m[valid] / boot_n_sw[valid]
                s2_cluster_ci = (float(np.percentile(s2_boots, 2.5)), float(np.percentile(s2_boots, 97.5)))
            else:
                s2_cluster_ci = s2_wilson_ci
        else:
            s2_cluster_ci = s2_wilson_ci
    else:
        n_assim = 0
        s2_rate = None
        s2_wilson_ci = (float("nan"), float("nan"))
        s2_cluster_ci = (float("nan"), float("nan"))

    return {
        "headroom_n": n_r,
        "susceptibility_rate": s1_rate,
        "susceptibility_ci_lower": s1_ci[0],
        "susceptibility_ci_upper": s1_ci[1],
        "switches_n": n_switches,
        "assimilation_n": n_assim,
        "assimilation_share": s2_rate,
        "assimilation_wilson_ci_lower": s2_wilson_ci[0] if n_switches > 0 else None,
        "assimilation_wilson_ci_upper": s2_wilson_ci[1] if n_switches > 0 else None,
        "assimilation_cluster_ci_lower": s2_cluster_ci[0] if n_switches > 0 else None,
        "assimilation_cluster_ci_upper": s2_cluster_ci[1] if n_switches > 0 else None,
        "compliance_share": 1.0 - s2_rate if s2_rate is not None else None,
    }


def compute_destabilization_metrics(df_pairs: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes gross vs net decision destabilization metrics from paired (control, pressure)
    observations. Binomial p-values are ORDER-LEVEL DESCRIPTIVE and treat each
    (scenario, option_order) observation as a trial. They do NOT account for
    within-scenario clustering and should not be cited as inferential tests.
    """
    n_matched = len(df_pairs)
    if n_matched == 0:
        return {
            "n_matched": 0, "n_changed": 0, "n_targetward": 0, "n_away": 0,
            "gross_change_rate": 0.0, "net_shift": 0.0, "directionality_ratio": 0.0,
            "p_targetward_given_changed": float("nan"),
            "binomial_pvalue_descriptive": float("nan")
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
        # Order-level descriptive binomial test (does NOT account for scenario clustering)
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
        "binomial_pvalue_descriptive": p_value
    }


def detect_missing_cells_from_manifest(manifest_df: pd.DataFrame, observed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies terminal missing cells by comparing scenario_manifest.csv against
    observed results. Use the FULL parsed dataset (df_master, all 2,290 rows)
    as observed_df — NOT df_primary (2,276 direct-valid only) — so that
    format-retry successes are not mislabeled as terminal failures.
    """
    observed_ids = set(observed_df["cell_id"])
    missing_df = manifest_df[~manifest_df["cell_id"].isin(observed_ids)].copy()
    return missing_df


def compute_missingness_bounds(
    df_observed: pd.DataFrame,
    missing_df: pd.DataFrame,
    model_id: str,
    treatment_id: str,
    control_id: str
) -> Dict[str, Any]:
    """
    Computes lower and upper sensitivity bounds for treatment action delta (ΔA)
    under extreme missing-data assumptions. Varies BOTH pressure AND control
    missing cells to produce the widest defensible interval.

    Lower bound: missing P → 0 AND missing C → 1 (minimizes ΔA)
    Upper bound: missing P → 1 AND missing C → 0 (maximizes ΔA)
    """
    p_obs = df_observed[(df_observed["model_id"] == model_id) & (df_observed["treatment_id"] == treatment_id)]
    c_obs = df_observed[(df_observed["model_id"] == model_id) & (df_observed["treatment_id"] == control_id)]

    n_p_obs = len(p_obs)
    n_c_obs = len(c_obs)

    p_missing = missing_df[(missing_df["model_id"] == model_id) & (missing_df["treatment_id"] == treatment_id)]
    c_missing = missing_df[(missing_df["model_id"] == model_id) & (missing_df["treatment_id"] == control_id)]
    n_p_miss = len(p_missing)
    n_c_miss = len(c_missing)

    if n_p_obs == 0 and n_c_obs == 0:
        return {
            "model_id": model_id, "treatment_id": treatment_id, "control_id": control_id,
            "n_p_observed": 0, "n_p_missing": n_p_miss,
            "n_c_observed": 0, "n_c_missing": n_c_miss,
            "delta_observed": float("nan"),
            "delta_lower_bound": float("nan"),
            "delta_upper_bound": float("nan"),
        }

    p_target_sum = int(p_obs["is_target_action"].sum()) if n_p_obs > 0 else 0
    c_target_sum = int(c_obs["is_target_action"].sum()) if n_c_obs > 0 else 0

    # Observed delta (using only observed cells)
    p_rate_obs = p_target_sum / n_p_obs if n_p_obs > 0 else 0.0
    c_rate_obs = c_target_sum / n_c_obs if n_c_obs > 0 else 0.0
    delta_obs = float(p_rate_obs - c_rate_obs)

    # Lower bound: missing P → 0 (deflate pressure), missing C → 1 (inflate control)
    p_rate_lower = p_target_sum / (n_p_obs + n_p_miss) if (n_p_obs + n_p_miss) > 0 else 0.0
    c_rate_upper = (c_target_sum + n_c_miss) / (n_c_obs + n_c_miss) if (n_c_obs + n_c_miss) > 0 else 0.0
    delta_lower = float(p_rate_lower - c_rate_upper)

    # Upper bound: missing P → 1 (inflate pressure), missing C → 0 (deflate control)
    p_rate_upper = (p_target_sum + n_p_miss) / (n_p_obs + n_p_miss) if (n_p_obs + n_p_miss) > 0 else 0.0
    c_rate_lower = c_target_sum / (n_c_obs + n_c_miss) if (n_c_obs + n_c_miss) > 0 else 0.0
    delta_upper = float(p_rate_upper - c_rate_lower)

    return {
        "model_id": model_id,
        "treatment_id": treatment_id,
        "control_id": control_id,
        "n_p_observed": n_p_obs,
        "n_p_missing": n_p_miss,
        "n_c_observed": n_c_obs,
        "n_c_missing": n_c_miss,
        "delta_observed": delta_obs,
        "delta_lower_bound": delta_lower,
        "delta_upper_bound": delta_upper,
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
