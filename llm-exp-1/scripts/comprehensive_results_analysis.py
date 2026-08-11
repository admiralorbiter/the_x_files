"""
IMPACT Study 1 — Comprehensive Results Analysis
Produces scenario-level paired inference, bootstrap CIs, qualitative examples,
and head-to-head model comparisons.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import random

random.seed(42)
np.random.seed(42)

RUN = Path("results/runs/20260809_233031_study_1_production")
reg = pd.read_csv(RUN / "scenario_registry.csv")
df_all = pd.read_csv(RUN / "study_1_production_results.csv")

# Filter to primary only
df = df_all[df_all["status"] == "COMPLETED"].copy()

# ============================================================
# PART A: SCENARIO-LEVEL PAIRED INFERENCE WITH BOOTSTRAP CIs
# ============================================================
print("=" * 90)
print("PART A: SCENARIO-LEVEL PAIRED INFERENCE WITH BOOTSTRAP CIs")
print("=" * 90)

families = {
    "P1_authority_pressure": "C1_authority_neutral",
    "P2_incentive_pressure": "C2_incentive_neutral",
    "P3_social_pressure": "C3_social_neutral",
    "P4_metric_pressure": "C4_metric_neutral",
}

def compute_scenario_paired_delta(m_df, p_id, c_id, outcome="is_target_action"):
    """Compute scenario-level paired differences, matching on scenario+order."""
    p_sub = m_df[m_df["treatment_id"] == p_id][["scenario_id", "choice_order_reversed", outcome]].copy()
    c_sub = m_df[m_df["treatment_id"] == c_id][["scenario_id", "choice_order_reversed", outcome]].copy()
    
    merged = pd.merge(p_sub, c_sub, on=["scenario_id", "choice_order_reversed"], suffixes=("_p", "_c"))
    merged["delta"] = merged[f"{outcome}_p"] - merged[f"{outcome}_c"]
    
    # Aggregate to scenario level (average across option orders within scenario)
    scenario_deltas = merged.groupby("scenario_id")["delta"].mean()
    return scenario_deltas

def bootstrap_ci(scenario_deltas, n_boot=10000, alpha=0.05):
    """Compute scenario-bootstrap confidence interval."""
    n = len(scenario_deltas)
    vals = scenario_deltas.values
    boot_means = np.array([np.mean(np.random.choice(vals, size=n, replace=True)) for _ in range(n_boot)])
    lower = np.percentile(boot_means, 100 * alpha / 2)
    upper = np.percentile(boot_means, 100 * (1 - alpha / 2))
    return lower, upper

def sign_test(scenario_deltas):
    """Simple sign test: count positive vs negative vs zero."""
    pos = (scenario_deltas > 0).sum()
    neg = (scenario_deltas < 0).sum()
    zero = (scenario_deltas == 0).sum()
    return pos, neg, zero

print("\n--- Scenario-Level Paired Deltas with Bootstrap 95% CIs ---")
print(f"{'Model':12s} | {'Mechanism':25s} | {'Mean dA':8s} | {'95% CI':20s} | {'Mean dJ':8s} | {'Mean dCC':8s} | Sign(+/−/0)")
print("-" * 115)

results_rows = []
for model in sorted(df["model_id"].unique()):
    m_df = df[df["model_id"] == model]
    for p_id, c_id in families.items():
        # Action delta
        sd_a = compute_scenario_paired_delta(m_df, p_id, c_id, "is_target_action")
        ci_a = bootstrap_ci(sd_a)
        sign_a = sign_test(sd_a)
        
        # Judgment delta
        sd_j = compute_scenario_paired_delta(m_df, p_id, c_id, "is_target_judgment")
        
        # CC delta: compute P(A=T, J!=T) for each
        p_sub = m_df[m_df["treatment_id"] == p_id].copy()
        c_sub = m_df[m_df["treatment_id"] == c_id].copy()
        p_sub["cc"] = ((p_sub["is_target_action"] == 1) & (p_sub["is_target_judgment"] == 0)).astype(int)
        c_sub["cc"] = ((c_sub["is_target_action"] == 1) & (c_sub["is_target_judgment"] == 0)).astype(int)
        
        p_cc = p_sub[["scenario_id", "choice_order_reversed", "cc"]]
        c_cc = c_sub[["scenario_id", "choice_order_reversed", "cc"]]
        cc_merged = pd.merge(p_cc, c_cc, on=["scenario_id", "choice_order_reversed"], suffixes=("_p", "_c"))
        cc_merged["delta_cc"] = cc_merged["cc_p"] - cc_merged["cc_c"]
        sd_cc = cc_merged.groupby("scenario_id")["delta_cc"].mean()
        
        mean_a = sd_a.mean()
        mean_j = sd_j.mean()
        mean_cc = sd_cc.mean()
        
        ci_str = f"[{ci_a[0]:+.3f}, {ci_a[1]:+.3f}]"
        sign_str = f"{sign_a[0]}/{sign_a[1]}/{sign_a[2]}"
        
        print(f"{model:12s} | {p_id:25s} | {mean_a:+8.3f} | {ci_str:20s} | {mean_j:+8.3f} | {mean_cc:+8.3f} | {sign_str}")
        
        results_rows.append({
            "model": model, "mechanism": p_id,
            "delta_action": mean_a, "ci_lower": ci_a[0], "ci_upper": ci_a[1],
            "delta_judgment": mean_j, "delta_cc": mean_cc,
            "sign_pos": sign_a[0], "sign_neg": sign_a[1], "sign_zero": sign_a[2],
            "n_scenarios": len(sd_a)
        })

# Save results
results_df = pd.DataFrame(results_rows)
results_df.to_csv(RUN / "scenario_paired_results.csv", index=False)

# ============================================================
# PART B: FACTORIAL BREAKDOWN (STRATUM x RELATION x MODEL)
# ============================================================
print("\n" + "=" * 90)
print("PART B: FACTORIAL BREAKDOWN — AUTHORITY EFFECT BY STRATUM x RELATION")
print("=" * 90)

for model in sorted(df["model_id"].unique()):
    m_df = df[df["model_id"] == model]
    print(f"\n--- {model} ---")
    print(f"{'Stratum':10s} | {'Relation':10s} | {'B0':7s} | {'C1':7s} | {'P1':7s} | {'dA':8s} | {'dJ':8s} | {'dCC':8s} | {'n_P1':5s} | {'n_C1':5s}")
    print("-" * 95)
    
    for stratum in ["Unanimous", "Divided"]:
        for relation in ["majority", "minority"]:
            sub = m_df[(m_df["agreement_stratum"] == stratum) & (m_df["target_relation_to_human"] == relation)]
            
            b0 = sub[sub["treatment_id"] == "B0_stripped_baseline"]
            c1 = sub[sub["treatment_id"] == "C1_authority_neutral"]
            p1 = sub[sub["treatment_id"] == "P1_authority_pressure"]
            
            b0_a = b0["is_target_action"].mean()
            c1_a = c1["is_target_action"].mean()
            p1_a = p1["is_target_action"].mean()
            da = p1_a - c1_a
            
            c1_j = c1["is_target_judgment"].mean()
            p1_j = p1["is_target_judgment"].mean()
            dj = p1_j - c1_j
            
            p1_cc = ((p1["is_target_action"] == 1) & (p1["is_target_judgment"] == 0)).mean()
            c1_cc = ((c1["is_target_action"] == 1) & (c1["is_target_judgment"] == 0)).mean()
            dcc = p1_cc - c1_cc
            
            print(f"{stratum:10s} | {relation:10s} | {b0_a:7.3f} | {c1_a:7.3f} | {p1_a:7.3f} | {da:+8.3f} | {dj:+8.3f} | {dcc:+8.3f} | {len(p1):5d} | {len(c1):5d}")

# ============================================================
# PART C: QUALITATIVE DEEP DIVE — DIVERGENCE CASE EXAMPLES
# ============================================================
print("\n" + "=" * 90)
print("PART C: QUALITATIVE DEEP DIVE — COMPLIANCE-WITHOUT-CONVICTION EXAMPLES")
print("=" * 90)

# Get all primary divergence cases where A=Target, J!=Target (compliance-without-conviction)
cc_cases = df[(df["is_target_action"] == 1) & (df["is_target_judgment"] == 0) & (df["divergence"] == 1)].copy()

print(f"\nTotal compliance-without-conviction cases (primary): {len(cc_cases)}")
print(f"  Under P1 authority: {(cc_cases['treatment_id'] == 'P1_authority_pressure').sum()}")
print(f"  Under P4 metric: {(cc_cases['treatment_id'] == 'P4_metric_pressure').sum()}")
print(f"  Other: {((cc_cases['treatment_id'] != 'P1_authority_pressure') & (cc_cases['treatment_id'] != 'P4_metric_pressure')).sum()}")

# Show the best examples — healthcare, corporate, government
print("\n--- CURATED COMPLIANCE-WITHOUT-CONVICTION RATIONALE TRACES ---")

# Group by scenario for interesting cases
for scenario_id in cc_cases["scenario_id"].unique():
    s_cases = cc_cases[cc_cases["scenario_id"] == scenario_id]
    s_reg = reg[reg["scenario_id"] == scenario_id].iloc[0]
    
    # Only show scenarios with multiple divergence instances
    if len(s_cases) < 2:
        continue
    
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_id} | Domain: {s_reg['domain']} | Role: {s_reg['decision_maker_role']}")
    print(f"Stratum: {'Unanimous (3/3)' if s_reg['human_entropy'] == 0 else 'Divided (2/1)'} | Target Relation: {s_reg['target_relation_to_human']}")
    print(f"Target Option: {s_reg['pressure_target_option']}")
    print(f"Kernel: {s_reg['ethical_kernel'][:200]}...")
    print(f"Option A: {s_reg['option_a'][:120]}...")
    print(f"Option B: {s_reg['option_b'][:120]}...")
    print(f"Human votes: P(A)={s_reg['human_prob_a']:.3f}, P(B)={s_reg['human_prob_b']:.3f}")
    
    for _, row in s_cases.iterrows():
        rev = row["choice_order_reversed"]
        print(f"\n  [{row['model_id']}] Treatment: {row['treatment_id']} | Order reversed: {rev}")
        print(f"  Explicit Moral Judgment: {row['parsed_judgment']} (semantic: {row['semantic_judgment']})")
        print(f"  Recommended Action:     {row['parsed_action']} (semantic: {row['semantic_action']})")
        print(f"  Rationale: {str(row['parsed_rationale'])[:300]}")

# ============================================================
# PART D: HEAD-TO-HEAD — SAME SCENARIO, QWEN VS GEMMA
# ============================================================
print("\n" + "=" * 90)
print("PART D: HEAD-TO-HEAD MODEL COMPARISON — SAME SCENARIO UNDER AUTHORITY")
print("=" * 90)

# Find scenarios where Qwen diverges but Gemma does not (or vice versa)
auth_df = df[df["treatment_id"] == "P1_authority_pressure"].copy()

# Pick minority-target scenarios for maximum contrast
minority_auth = auth_df[auth_df["target_relation_to_human"] == "minority"]

# Group by scenario
for scen_id in sorted(minority_auth["scenario_id"].unique())[:8]:
    s_reg = reg[reg["scenario_id"] == scen_id].iloc[0]
    s_data = minority_auth[minority_auth["scenario_id"] == scen_id]
    
    qwen_data = s_data[s_data["model_id"] == "qwen3:14b"]
    gemma_data = s_data[s_data["model_id"] == "gemma4:12b"]
    
    if len(qwen_data) == 0 or len(gemma_data) == 0:
        continue
    
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scen_id} | {s_reg['domain']} | {s_reg['decision_maker_role']} | Target: {s_reg['pressure_target_option']} (minority)")
    print(f"Kernel: {s_reg['ethical_kernel'][:200]}...")
    
    for _, row in qwen_data.iterrows():
        div_mark = " *** DIVERGENCE ***" if row["divergence"] == 1 else ""
        print(f"\n  QWEN (rev={row['choice_order_reversed']}): J={row['parsed_judgment']}(sem:{row['semantic_judgment']}) A={row['parsed_action']}(sem:{row['semantic_action']}){div_mark}")
        print(f"    {str(row['parsed_rationale'])[:250]}")
    
    for _, row in gemma_data.iterrows():
        div_mark = " *** DIVERGENCE ***" if row["divergence"] == 1 else ""
        print(f"\n  GEMMA (rev={row['choice_order_reversed']}): J={row['parsed_judgment']}(sem:{row['semantic_judgment']}) A={row['parsed_action']}(sem:{row['semantic_action']}){div_mark}")
        print(f"    {str(row['parsed_rationale'])[:250]}")

# ============================================================
# PART E: SCENARIO-LEVEL AUTHORITY EFFECT RANKING
# ============================================================
print("\n" + "=" * 90)
print("PART E: SCENARIO-LEVEL AUTHORITY EFFECT RANKING (QWEN)")
print("=" * 90)

qwen_df = df[df["model_id"] == "qwen3:14b"]
sd_auth_qwen = compute_scenario_paired_delta(qwen_df, "P1_authority_pressure", "C1_authority_neutral", "is_target_action")
sd_auth_qwen = sd_auth_qwen.sort_values(ascending=False)

print(f"\n{'Scenario':15s} | {'dA':8s} | {'Domain':25s} | {'Role':20s} | {'Stratum':12s} | {'Relation':10s}")
print("-" * 100)

for scen_id, delta in sd_auth_qwen.items():
    s_reg = reg[reg["scenario_id"] == scen_id].iloc[0]
    strat = "Unanimous" if s_reg["human_entropy"] == 0 else "Divided"
    print(f"{scen_id:15s} | {delta:+8.3f} | {s_reg['domain']:25s} | {s_reg['decision_maker_role']:20s} | {strat:12s} | {s_reg['target_relation_to_human']:10s}")

# ============================================================
# PART F: NON-AUTHORITY PRESSURE — METRIC DEEP DIVE
# ============================================================
print("\n" + "=" * 90)
print("PART F: METRIC PRESSURE (P4) DEEP DIVE — QWEN")
print("=" * 90)

sd_metric_qwen = compute_scenario_paired_delta(qwen_df, "P4_metric_pressure", "C4_metric_neutral", "is_target_action")
sd_metric_qwen = sd_metric_qwen.sort_values(ascending=False)

print(f"\nScenarios with positive metric effect (top 15):")
print(f"{'Scenario':15s} | {'dA':8s} | {'Domain':25s} | {'Stratum':12s} | {'Relation':10s}")
print("-" * 80)
for scen_id, delta in sd_metric_qwen.head(15).items():
    s_reg = reg[reg["scenario_id"] == scen_id].iloc[0]
    strat = "Unanimous" if s_reg["human_entropy"] == 0 else "Divided"
    print(f"{scen_id:15s} | {delta:+8.3f} | {s_reg['domain']:25s} | {strat:12s} | {s_reg['target_relation_to_human']:10s}")

# Metric divergence examples
metric_cc = cc_cases[cc_cases["treatment_id"] == "P4_metric_pressure"]
print(f"\nMetric compliance-without-conviction examples ({len(metric_cc)} cases):")
for _, row in metric_cc.head(5).iterrows():
    print(f"\n  [{row['model_id']}] {row['scenario_id']} ({row['domain']}, {row['decision_maker_role']})")
    print(f"  J={row['parsed_judgment']}(sem:{row['semantic_judgment']}) A={row['parsed_action']}(sem:{row['semantic_action']})")
    print(f"  Rationale: {str(row['parsed_rationale'])[:250]}")

print("\n" + "=" * 90)
print("ANALYSIS COMPLETE")
print("=" * 90)
