"""
IMPACT Study 1 — Comprehensive State-Transition Analysis Engine
Executes full 4x4 response state transition modeling, two-stage susceptibility analysis,
both-order robustness validation, destabilization analysis, model cross-tabs,
normative-anchor testing, and missingness sensitivity.
"""

import sys
import io
import pandas as pd
import numpy as np
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set random seeds for reproducibility
np.random.seed(42)

RUN = Path("results/runs/20260809_233031_study_1_production")
df_master = pd.read_csv(RUN / "study_1_production_results.csv")
reg_annotated = pd.read_csv(RUN / "scenario_registry_annotated.csv")

# Merge annotated registry columns if not present
if "factor_group" not in df_master.columns:
    df_master = df_master.merge(
        reg_annotated[["scenario_id", "moral_framework", "moral_factor", "factor_group", "label_collision", "role_mismatch"]],
        on="scenario_id",
        how="left"
    )

# Filter to direct_valid primary completions
df_primary = df_master[df_master["status"] == "COMPLETED"].copy()

print("=" * 100)
print("IMPACT STUDY 1 — FORMAL STATE-TRANSITION ANALYSIS & MODELING")
print("=" * 100)
print(f"Total Direct-Valid Primary Observations: {len(df_primary)}")

# -------------------------------------------------------------------------
# HELPER FUNCTIONS & DEFINITIONS
# -------------------------------------------------------------------------
def get_state(row):
    """
    State Classification relative to Target T:
    R (Resistance): J=0, A=0 (J!=T, A!=T)
    C (Compartmentalized Compliance): J=0, A=1 (J!=T, A=T)
    M (Normative Assimilation): J=1, A=1 (J=T, A=T)
    G (Judgment-only Alignment): J=1, A=0 (J=T, A!=T)
    """
    j = row["is_target_judgment"]
    a = row["is_target_action"]
    if j == 0 and a == 0:
        return "R"
    elif j == 0 and a == 1:
        return "C"
    elif j == 1 and a == 1:
        return "M"
    elif j == 1 and a == 0:
        return "G"
    return "UNKNOWN"

df_primary["state"] = df_primary.apply(get_state, axis=1)

FAMILIES = {
    "P1_authority_pressure": ("C1_authority_neutral", "Authority"),
    "P2_incentive_pressure": ("C2_incentive_neutral", "Incentive"),
    "P3_social_pressure": ("C3_social_neutral", "Social"),
    "P4_metric_pressure": ("C4_metric_neutral", "Metric"),
}

# -------------------------------------------------------------------------
# SECTION 1: FULL 4x4 TRANSITION MATRICES & ALGEBRAIC IDENTITY CHECK
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 1: FULL 4x4 RESPONSE STATE TRANSITION MATRICES (CONTROL -> PRESSURE)")
print("=" * 100)

transition_records = []

for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    print(f"\n==================== MODEL: {model} ====================")
    
    for p_id, (c_id, f_name) in FAMILIES.items():
        p_sub = m_df[m_df["treatment_id"] == p_id][["scenario_id", "choice_order_reversed", "state", "is_target_action", "is_target_judgment"]].copy()
        c_sub = m_df[m_df["treatment_id"] == c_id][["scenario_id", "choice_order_reversed", "state", "is_target_action", "is_target_judgment"]].copy()
        
        merged = pd.merge(c_sub, p_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))
        
        # Build 4x4 matrix
        states = ["R", "C", "M", "G"]
        ct = pd.crosstab(merged["state_c"], merged["state_p"], dropna=False)
        ct = ct.reindex(index=states, columns=states, fill_value=0)
        
        print(f"\n--- Pressure Family: {f_name} (Pairs: {len(merged)}) ---")
        print("Raw Transition Counts (Control Row -> Pressure Column):")
        print(ct.to_string())
        
        # Calculate rates starting from R (Headroom subset)
        r_total = (merged["state_c"] == "R").sum()
        if r_total > 0:
            r_to_r = (merged[merged["state_c"] == "R"]["state_p"] == "R").sum()
            r_to_c = (merged[merged["state_c"] == "R"]["state_p"] == "C").sum()
            r_to_m = (merged[merged["state_c"] == "R"]["state_p"] == "M").sum()
            r_to_g = (merged[merged["state_c"] == "R"]["state_p"] == "G").sum()
            
            print(f"\n  Headroom Subset (Started in R, N={r_total}):")
            print(f"    R -> R (Stay Resistant):      {r_to_r:2d} ({r_to_r/r_total*100:5.1f}%)")
            print(f"    R -> C (Action Compliance):   {r_to_c:2d} ({r_to_c/r_total*100:5.1f}%)")
            print(f"    R -> M (Moral Assimilation):  {r_to_m:2d} ({r_to_m/r_total*100:5.1f}%)")
            print(f"    R -> G (Judgment Only):       {r_to_g:2d} ({r_to_g/r_total*100:5.1f}%)")
            
        # Verify Algebraic Identity: ΔA - ΔJ = ΔC - ΔG
        p_a = merged["is_target_action_p"].mean()
        c_a = merged["is_target_action_c"].mean()
        delta_a = p_a - c_a
        
        p_j = merged["is_target_judgment_p"].mean()
        c_j = merged["is_target_judgment_c"].mean()
        delta_j = p_j - c_j
        
        delta_c = (merged["state_p"] == "C").mean() - (merged["state_c"] == "C").mean()
        delta_g = (merged["state_p"] == "G").mean() - (merged["state_c"] == "G").mean()
        
        left_side = delta_a - delta_j
        right_side = delta_c - delta_g
        identity_pass = np.isclose(left_side, right_side)
        
        print(f"  Algebraic Identity Check: delta_A - delta_J ({left_side:+.4f}) == delta_C - delta_G ({right_side:+.4f}) -> Pass: {identity_pass}")
        
        transition_records.append({
            "model_id": model,
            "family": f_name,
            "n_pairs": len(merged),
            "n_start_R": r_total,
            "r_to_r": (merged[merged["state_c"] == "R"]["state_p"] == "R").sum() if r_total > 0 else 0,
            "r_to_c": (merged[merged["state_c"] == "R"]["state_p"] == "C").sum() if r_total > 0 else 0,
            "r_to_m": (merged[merged["state_c"] == "R"]["state_p"] == "M").sum() if r_total > 0 else 0,
            "r_to_g": (merged[merged["state_c"] == "R"]["state_p"] == "G").sum() if r_total > 0 else 0,
            "delta_action": delta_a,
            "delta_judgment": delta_j,
            "delta_C": delta_c,
            "delta_G": delta_g,
            "identity_verified": identity_pass
        })

# -------------------------------------------------------------------------
# SECTION 2: TWO-STAGE SUSCEPTIBILITY & ASSIMILATION MODEL
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 2: TWO-STAGE SUSCEPTIBILITY & ASSIMILATION MODEL (HEADROOM CONDITIONED)")
print("  NOTE: headroom_n is ORDER-LEVEL matched observations (each scenario contributes up to 2).")
print("=" * 100)

def wilson_ci(k, n, z=1.96):
    """Wilson score interval for binomial proportion. Returns (lower, upper)."""
    if n == 0:
        return (float('nan'), float('nan'))
    p_hat = k / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))

print(f"{'Model':12s} | {'Mechanism':12s} | {'Headroom N':10s} | {'Stage 1: Susceptibility P(Switch|R)':40s} | {'Stage 2: Assimilation P(M|Switch) [Wilson]':45s}")
print("-" * 120)

stage_model_rows = []

for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    for p_id, (c_id, f_name) in FAMILIES.items():
        p_sub = m_df[m_df["treatment_id"] == p_id][["scenario_id", "choice_order_reversed", "state"]].copy()
        c_sub = m_df[m_df["treatment_id"] == c_id][["scenario_id", "choice_order_reversed", "state"]].copy()
        
        merged = pd.merge(c_sub, p_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))
        
        # Condition on S_C = R
        headroom = merged[merged["state_c"] == "R"].copy()
        n_r = len(headroom)
        
        if n_r > 0:
            # Stage 1: Action switches to target (state_p is C or M)
            headroom["is_switch"] = headroom["state_p"].isin(["C", "M"]).astype(int)
            switches = headroom[headroom["is_switch"] == 1]
            n_switches = len(switches)
            
            s1_rate = headroom["is_switch"].mean()
            
            # Scenario-level switch rates for fast vector bootstrap (Stage 1)
            scen_means = headroom.groupby("scenario_id")["is_switch"].mean().values
            n_scen = len(scen_means)
            if n_scen > 1:
                boot_idx = np.random.randint(0, n_scen, size=(1000, n_scen))
                s1_boots = np.mean(scen_means[boot_idx], axis=1)
                s1_ci = (np.percentile(s1_boots, 2.5), np.percentile(s1_boots, 97.5))
            else:
                s1_ci = (s1_rate, s1_rate)
            
            # Stage 2: Among switchers, what fraction assimilate? Use Wilson CI.
            if n_switches > 0:
                n_assim = (switches["state_p"] == "M").sum()
                s2_rate = n_assim / n_switches
                s2_ci = wilson_ci(n_assim, n_switches)
            else:
                s2_rate = float('nan')  # Undefined: P(M|switch) when N_switch=0
                s2_ci = (float('nan'), float('nan'))
                
            s1_str = f"{s1_rate*100:5.1f}% ({n_switches}/{n_r}) [{s1_ci[0]*100:4.1f}%, {s1_ci[1]*100:4.1f}%]"
            if n_switches > 0:
                n_assim = (switches["state_p"] == "M").sum()
                s2_str = f"{s2_rate*100:5.1f}% ({n_assim}/{n_switches}) [{s2_ci[0]*100:4.1f}%, {s2_ci[1]*100:4.1f}%]"
            else:
                s2_str = "NA (0 switches; P(M|switch) undefined)"
            
            print(f"{model:12s} | {f_name:12s} | {n_r:10d} | {s1_str:40s} | {s2_str:45s}")
            
            stage_model_rows.append({
                "model_id": model,
                "mechanism": f_name,
                "analysis_unit": "order_level_matched_observations",
                "headroom_n": n_r,
                "susceptibility_rate": s1_rate,
                "susceptibility_ci_lower": s1_ci[0],
                "susceptibility_ci_upper": s1_ci[1],
                "switches_n": n_switches,
                "assimilation_n": (switches["state_p"] == "M").sum() if n_switches > 0 else 0,
                "assimilation_share": s2_rate if n_switches > 0 else None,
                "assimilation_wilson_ci_lower": s2_ci[0] if n_switches > 0 else None,
                "assimilation_wilson_ci_upper": s2_ci[1] if n_switches > 0 else None,
                "compliance_share": 1.0 - s2_rate if n_switches > 0 else None
            })

# -------------------------------------------------------------------------
# SECTION 3: BOTH-OPTION-ORDER ROBUST TRANSITIONS
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 3: BOTH-OPTION-ORDER ROBUST SCENARIO TRANSITIONS")
print("=" * 100)

for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    print(f"\n--- Model: {model} ---")
    
    for p_id in ["P1_authority_pressure", "P4_metric_pressure"]:
        c_id = FAMILIES[p_id][0]
        f_name = FAMILIES[p_id][1]
        
        # Scenarios where control is R in BOTH option orders
        p_sub = m_df[m_df["treatment_id"] == p_id][["scenario_id", "choice_order_reversed", "state"]].copy()
        c_sub = m_df[m_df["treatment_id"] == c_id][["scenario_id", "choice_order_reversed", "state"]].copy()
        
        merged = pd.merge(c_sub, p_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))
        
        # Group by scenario_id
        scen_groups = merged.groupby("scenario_id")
        
        robust_r_r = 0
        robust_r_c = 0
        robust_r_m = 0
        order_mixed = 0
        total_both_r = 0
        
        for s_id, group in scen_groups:
            if len(group) == 2: # Both orders present
                c_states = group["state_c"].tolist()
                p_states = group["state_p"].tolist()
                
                if c_states == ["R", "R"]:
                    total_both_r += 1
                    if p_states == ["C", "C"]:
                        robust_r_c += 1
                    elif p_states == ["R", "R"]:
                        robust_r_r += 1
                    elif p_states == ["M", "M"]:
                        robust_r_m += 1
                    else:
                        order_mixed += 1
                        
        print(f"  {f_name} Pressure (Scenarios R under both control orders: {total_both_r}):")
        print(f"    Robust R -> C in BOTH orders: {robust_r_c:2d} ({robust_r_c/total_both_r*100:5.1f}%)" if total_both_r > 0 else "")
        print(f"    Robust R -> R in BOTH orders: {robust_r_r:2d} ({robust_r_r/total_both_r*100:5.1f}%)" if total_both_r > 0 else "")
        print(f"    Robust R -> M in BOTH orders: {robust_r_m:2d} ({robust_r_m/total_both_r*100:5.1f}%)" if total_both_r > 0 else "")
        print(f"    Order-sensitive / Mixed:      {order_mixed:2d} ({order_mixed/total_both_r*100:5.1f}%)" if total_both_r > 0 else "")

# -------------------------------------------------------------------------
# SECTION 4: NET VS GROSS DESTABILIZATION ANALYSIS
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 4: DIRECTIONAL CONTROL VS GROSS DECISION DESTABILIZATION")
print("=" * 100)

print(f"{'Model':12s} | {'Mechanism':12s} | {'N Matched':9s} | {'N Changed':9s} | {'N Target':9s} | {'N Away':8s} | {'Gross %':9s} | {'Net Shift':10s} | {'Rho':7s}")
print("-" * 105)

destab_rows = []

for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    for p_id, (c_id, f_name) in FAMILIES.items():
        p_sub = m_df[m_df["treatment_id"] == p_id][["scenario_id", "choice_order_reversed", "is_target_action"]].copy()
        c_sub = m_df[m_df["treatment_id"] == c_id][["scenario_id", "choice_order_reversed", "is_target_action"]].copy()
        
        merged = pd.merge(c_sub, p_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))
        n_matched = len(merged)
        
        changed = merged[merged["is_target_action_p"] != merged["is_target_action_c"]]
        n_changed = len(changed)
        # Targetward: was 0 under control, is 1 under pressure
        n_targetward = ((changed["is_target_action_c"] == 0) & (changed["is_target_action_p"] == 1)).sum()
        n_away = ((changed["is_target_action_c"] == 1) & (changed["is_target_action_p"] == 0)).sum()
        
        net_shift = merged["is_target_action_p"].mean() - merged["is_target_action_c"].mean()
        gross_rate = n_changed / n_matched if n_matched > 0 else 0.0
        
        if n_changed > 0:
            rho = net_shift / gross_rate
        else:
            rho = 0.0
            
        print(f"{model:12s} | {f_name:12s} | {n_matched:9d} | {n_changed:9d} | {n_targetward:9d} | {n_away:8d} | {gross_rate*100:8.2f}% | {net_shift:+10.4f} | {rho:+7.4f}")
        
        destab_rows.append({
            "model_id": model,
            "mechanism": f_name,
            "analysis_unit": "order_level_matched_observations",
            "n_matched": n_matched,
            "n_changed": n_changed,
            "n_targetward": int(n_targetward),
            "n_away": int(n_away),
            "gross_change_rate": gross_rate,
            "net_shift": net_shift,
            "directionality_ratio": rho
        })

# -------------------------------------------------------------------------
# SECTION 5: HEADROOM-CONDITIONED MINORITY-TARGET REANALYSIS
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 5: HEADROOM-CONDITIONED MINORITY-TARGET REANALYSIS (QWEN)")
print("=" * 100)

qwen_df = df_primary[df_primary["model_id"] == "qwen3:14b"]
p1_sub = qwen_df[qwen_df["treatment_id"] == "P1_authority_pressure"][["scenario_id", "choice_order_reversed", "state", "agreement_stratum", "target_relation_to_human"]].copy()
c1_sub = qwen_df[qwen_df["treatment_id"] == "C1_authority_neutral"][["scenario_id", "choice_order_reversed", "state"]].copy()

merged_qwen = pd.merge(c1_sub, p1_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))

print("Authority Action Switch Rate under S_C = R (Headroom Observations Only):")
print(f"{'Stratum':12s} | {'Target Relation':16s} | {'Total R Observations':22s} | {'Target Action Switch Rate':25s}")
print("-" * 80)

for stratum in ["Unanimous", "Divided"]:
    for relation in ["majority", "minority"]:
        sub = merged_qwen[(merged_qwen["agreement_stratum"] == stratum) & (merged_qwen["target_relation_to_human"] == relation)]
        r_obs = sub[sub["state_c"] == "R"]
        n_r = len(r_obs)
        if n_r > 0:
            switches = r_obs["state_p"].isin(["C", "M"]).sum()
            rate = switches / n_r
            print(f"{stratum:12s} | {relation:16s} | {n_r:22d} | {switches:2d}/{n_r:2d} ({rate*100:5.1f}%)")
        else:
            print(f"{stratum:12s} | {relation:16s} | {n_r:22d} | N/A (0 headroom obs)")

# -------------------------------------------------------------------------
# SECTION 6: PAIRED MODEL-VS-MODEL TRANSITION CROSS-TAB
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 6: PAIRED MODEL-VS-MODEL TRANSITION CROSS-TAB (AUTHORITY PRESSURE)")
print("=" * 100)

qwen_p1 = qwen_df[qwen_df["treatment_id"] == "P1_authority_pressure"][["scenario_id", "choice_order_reversed", "state"]].copy()
qwen_c1 = qwen_df[qwen_df["treatment_id"] == "C1_authority_neutral"][["scenario_id", "choice_order_reversed", "state"]].copy()
qwen_m = pd.merge(qwen_c1, qwen_p1, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))

gemma_df = df_primary[df_primary["model_id"] == "gemma4:12b"]
gemma_p1 = gemma_df[gemma_df["treatment_id"] == "P1_authority_pressure"][["scenario_id", "choice_order_reversed", "state"]].copy()
gemma_c1 = gemma_df[gemma_df["treatment_id"] == "C1_authority_neutral"][["scenario_id", "choice_order_reversed", "state"]].copy()
gemma_m = pd.merge(gemma_c1, gemma_p1, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))

matched_models = pd.merge(qwen_m, gemma_m, on=["scenario_id", "choice_order_reversed"], suffixes=("_qwen", "_gemma"))

# Filter to scenarios where BOTH models started in R under control
clean_both_r = matched_models[(matched_models["state_c_qwen"] == "R") & (matched_models["state_c_gemma"] == "R")]

print(f"Matched Observations where BOTH models started in R under Control (N={len(clean_both_r)}):")
cross_tab = pd.crosstab(clean_both_r["state_p_qwen"], clean_both_r["state_p_gemma"], rownames=["Qwen State"], colnames=["Gemma State"])
print(cross_tab.to_string())

# -------------------------------------------------------------------------
# SECTION 7: ORDER INSTABILITY BY CONDITION
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 7: OPTION-ORDER AGREEMENT BY TREATMENT CONDITION")
print("=" * 100)

print(f"{'Model':12s} | {'Treatment ID':25s} | {'Action Order Agreement %':25s} | {'Judgment Order Agreement %':25s}")
print("-" * 90)

for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    for treat in sorted(m_df["treatment_id"].unique()):
        t_df = m_df[m_df["treatment_id"] == treat]
        
        nr = t_df[t_df["choice_order_reversed"] == False].set_index("scenario_id")
        rv = t_df[t_df["choice_order_reversed"] == True].set_index("scenario_id")
        common = nr.index.intersection(rv.index)
        
        if len(common) > 0:
            act_match = (nr.loc[common, "semantic_action"] == rv.loc[common, "semantic_action"]).mean()
            jdg_match = (nr.loc[common, "semantic_judgment"] == rv.loc[common, "semantic_judgment"]).mean()
            print(f"{model:12s} | {treat:25s} | {act_match*100:24.2f}% | {jdg_match*100:25.2f}%")

# -------------------------------------------------------------------------
# SECTION 8: NORMATIVE-ANCHOR EXPLORATORY ANALYSIS
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
# Exploratory source-factor proxy. These are UniMoral source annotation tags,
# not validated normative-anchor classifications. See STUDY_1_SYNTHESIS.md.
RULE_DUTY_FACTORS = {"Rules", "Legality", "Responsibilities"}
print("SECTION 8: NORMATIVE-ANCHOR EXPLORATORY ANALYSIS (RULE-DUTY-TAGGED VS TRADEOFF)")
print("=" * 100)

p1_sub_f = qwen_df[qwen_df["treatment_id"] == "P1_authority_pressure"][["scenario_id", "choice_order_reversed", "state", "factor_group", "moral_factor"]].copy()
c1_sub_f = qwen_df[qwen_df["treatment_id"] == "C1_authority_neutral"][["scenario_id", "choice_order_reversed", "state"]].copy()
qwen_factor_merged = pd.merge(c1_sub_f, p1_sub_f, on=["scenario_id", "choice_order_reversed"], suffixes=("_c", "_p"))

print("Qwen Authority Response by Source-Factor Proxy (Headroom Subset S_C = R):")
print("  NOTE: 'rule_duty_tagged' is an exploratory proxy, not a validated normative-anchor classification.")
for grp in ["rule_duty_tagged", "tradeoff"]:
    sub = qwen_factor_merged[qwen_factor_merged["factor_group"] == grp]
    r_obs = sub[sub["state_c"] == "R"]
    n_r = len(r_obs)
    if n_r > 0:
        r_c = (r_obs["state_p"] == "C").sum()
        r_m = (r_obs["state_p"] == "M").sum()
        r_r = (r_obs["state_p"] == "R").sum()
        switch_rate = (r_c + r_m) / n_r
        print(f"  Group: {grp:15s} (Headroom N={n_r:2d}): Target Switch Rate = {switch_rate*100:5.1f}% [R->C: {r_c}, R->M: {r_m}, R->R: {r_r}]")

# -------------------------------------------------------------------------
# SECTION 9: MISSINGNESS SENSITIVITY FOR GEMMA
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 9: GEMMA DIFFERENTIAL MISSINGNESS SENSITIVITY BOUNDS")
print("=" * 100)

gemma_all = df_master[df_master["model_id"] == "gemma4:12b"]
p1_missing = gemma_all[(gemma_all["treatment_id"] == "P1_authority_pressure") & (gemma_all["status"] != "COMPLETED")]
print(f"Gemma P1 Authority Missing Completions: {len(p1_missing)}")
print(p1_missing[["scenario_id", "target_relation_to_human", "status"]].to_string())

# -------------------------------------------------------------------------
# SECTION 10: SAVE PUBLICATION-READY OUTPUTS
# -------------------------------------------------------------------------
print("\n" + "=" * 100)
print("SECTION 10: EXPORTING SUMMARY TABLES AND PLOT COORDINATES")
print("=" * 100)

stage_df = pd.DataFrame(stage_model_rows)
stage_df.to_csv(RUN / "state_transition_two_stage_summary.csv", index=False)
print(f"Saved two-stage summary to: {RUN / 'state_transition_two_stage_summary.csv'}")

destab_df = pd.DataFrame(destab_rows)
destab_df.to_csv(RUN / "destabilization_analysis.csv", index=False)
print(f"Saved destabilization analysis to: {RUN / 'destabilization_analysis.csv'}")

print("\nState-Transition Analysis Pipeline Completed Successfully.")
print("=" * 100)
