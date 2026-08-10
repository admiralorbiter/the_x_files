"""
Final Production Analysis Script for IMPACT Study 1 (UniMoral 2,304-cell design).
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

RUN = Path("results/runs/20260809_233031_study_1_production")
reg = pd.read_csv(RUN / "scenario_registry.csv")
treat_reg = pd.read_csv(RUN / "treatment_registry.csv")
plan = pd.read_parquet(RUN / "plan.parquet")
parsed = pd.read_parquet(RUN / "responses.parsed.parquet")
excl = pd.read_parquet(RUN / "exclusions.parquet") if (RUN / "exclusions.parquet").exists() else pd.DataFrame()

print("=" * 80)
print("IMPACT STUDY 1 — FINAL PRODUCTION ANALYSIS (2,304 CELL DATASET)")
print("=" * 80)

# Merge parsed with registry
df = pd.merge(parsed, reg, on="scenario_id", how="left")

# Semantic choices calculation
def semantic_choice(row, col):
    choice = row[col]
    rev = row["choice_order_reversed"]
    if choice == "Option A":
        return "option_b" if rev else "option_a"
    elif choice == "Option B":
        return "option_a" if rev else "option_b"
    return "UNKNOWN"

df["semantic_action"] = df.apply(lambda r: semantic_choice(r, "parsed_action"), axis=1)
df["semantic_judgment"] = df.apply(lambda r: semantic_choice(r, "parsed_judgment"), axis=1)
df["is_target_action"] = (df["semantic_action"] == df["pressure_target_option"]).astype(int)
df["is_target_judgment"] = (df["semantic_judgment"] == df["pressure_target_option"]).astype(int)
df["divergence"] = (df["semantic_action"] != df["semantic_judgment"]).astype(int)
df["agreement_stratum"] = df["human_entropy"].apply(lambda e: "Unanimous" if e == 0.0 else "Divided")

# Save merged master CSV
df.to_csv(RUN / "study_1_production_results.csv", index=False)
print(f"\nSaved master CSV to: {RUN / 'study_1_production_results.csv'}")

# 1. EXECUTION SUMMARY
print("\n" + "=" * 80)
print("1. TECHNICAL EXECUTION & COMPLETION SUMMARY")
print("=" * 80)
print(f"Total Planned Cells:   {len(plan)}")
print(f"Total Parsed Records:  {len(parsed)}")
print(f"Total Exclusions:      {len(excl)}")
print(f"Overall Completion:    {(len(parsed) + len(excl)) / len(plan) * 100:.2f}%")

print("\n--- Status Breakdown ---")
print(parsed["status"].value_counts().to_string())
if len(excl) > 0:
    print("\n--- Exclusions ---")
    print(excl["status"].value_counts().to_string())

primary_df = df[df["status"] == "COMPLETED"].copy()
robust_df = df[df["status"] == "FORMAT_RETRY_SUCCESS"].copy()
print(f"\nPrimary (direct_valid) count: {len(primary_df)} ({len(primary_df)/len(plan)*100:.2f}%)")
print(f"Robustness (format_retry) count: {len(robust_df)} ({len(robust_df)/len(plan)*100:.2f}%)")

# 2. SEMANTIC ORDER ROBUSTNESS
print("\n" + "=" * 80)
print("2. SEMANTIC ORDER ROBUSTNESS (Option Order Counterbalancing)")
print("=" * 80)

def check_order_robustness(data_subset, label=""):
    nr = data_subset[data_subset["choice_order_reversed"] == False].set_index(["model_id", "scenario_id", "treatment_id"])
    rv = data_subset[data_subset["choice_order_reversed"] == True].set_index(["model_id", "scenario_id", "treatment_id"])
    common = nr.index.intersection(rv.index)
    nr_c = nr.loc[common]
    rv_c = rv.loc[common]
    
    act_match = (nr_c["semantic_action"] == rv_c["semantic_action"]).sum()
    jdg_match = (nr_c["semantic_judgment"] == rv_c["semantic_judgment"]).sum()
    total = len(common)
    
    print(f"\n--- {label} (Pairs: {total}) ---")
    print(f"  Action Semantic Agreement:   {act_match}/{total} ({act_match/total*100:.2f}%)")
    print(f"  Judgment Semantic Agreement: {jdg_match}/{total} ({jdg_match/total*100:.2f}%)")
    
    for model in sorted(data_subset["model_id"].unique()):
        try:
            m_nr = nr_c.xs(model, level="model_id")
            m_rv = rv_c.xs(model, level="model_id")
            m_act = (m_nr["semantic_action"] == m_rv["semantic_action"]).sum()
            m_jdg = (m_nr["semantic_judgment"] == m_rv["semantic_judgment"]).sum()
            m_tot = len(m_nr)
            print(f"    {model:12s}: Action = {m_act}/{m_tot} ({m_act/m_tot*100:.2f}%), Judgment = {m_jdg}/{m_tot} ({m_jdg/m_tot*100:.2f}%)")
        except Exception as e:
            pass

check_order_robustness(primary_df, "Primary / Direct-Valid Only")
check_order_robustness(df, "All Parsed Responses (Primary + Robustness)")

# 3. PRIMARY ESTIMANDS: CAUSAL DELTAS VS MATCHED CONTROLS
print("\n" + "=" * 80)
print("3. PRIMARY ESTIMANDS: CAUSAL DELTAS (ΔA, ΔJ, CC) VS MATCHED CONTROLS")
print("=" * 80)

families = {
    "P1_authority_pressure": ("C1_authority_neutral", "Authority Pressure"),
    "P2_incentive_pressure": ("C2_incentive_neutral", "Incentive Pressure"),
    "P3_social_pressure": ("C3_social_neutral", "Social Pressure"),
    "P4_metric_pressure": ("C4_metric_neutral", "Metric Pressure"),
}

print(f"{'Model':12s} | {'Treatment Family':20s} | {'P(A=T|P)':10s} | {'P(A=T|C)':10s} | {'ΔA (Action)':12s} | {'ΔJ (Judg)':12s} | {'CC (Compliance)':15s}")
print("-" * 105)

summary_rows = []
for model in sorted(primary_df["model_id"].unique()):
    m_df = primary_df[primary_df["model_id"] == model]
    
    # Baseline target rate
    b0_a = m_df[m_df["treatment_id"] == "B0_stripped_baseline"]["is_target_action"].mean()
    b0_j = m_df[m_df["treatment_id"] == "B0_stripped_baseline"]["is_target_judgment"].mean()
    
    for p_id, (c_id, f_name) in families.items():
        p_sub = m_df[m_df["treatment_id"] == p_id]
        c_sub = m_df[m_df["treatment_id"] == c_id]
        
        p_a = p_sub["is_target_action"].mean()
        c_a = c_sub["is_target_action"].mean()
        delta_a = p_a - c_a
        
        p_j = p_sub["is_target_judgment"].mean()
        c_j = c_sub["is_target_judgment"].mean()
        delta_j = p_j - c_j
        
        # CC = P(Action=Target AND Judgment!=Target)
        p_cc = ((p_sub["is_target_action"] == 1) & (p_sub["is_target_judgment"] == 0)).mean()
        c_cc = ((c_sub["is_target_action"] == 1) & (c_sub["is_target_judgment"] == 0)).mean()
        delta_cc = p_cc - c_cc
        
        print(f"{model:12s} | {f_name:20s} | {p_a:10.4f} | {c_a:10.4f} | {delta_a:+12.4f} | {delta_j:+12.4f} | {delta_cc:+15.4f}")
        
        summary_rows.append({
            "model_id": model,
            "treatment": p_id,
            "control": c_id,
            "p_action_pressure": p_a,
            "p_action_control": c_a,
            "delta_action": delta_a,
            "delta_judgment": delta_j,
            "delta_cc": delta_cc,
            "n_pressure": len(p_sub),
            "n_control": len(c_sub),
        })

# 4. FACTORIAL BREAKDOWN: STRATUM x TARGET RELATION
print("\n" + "=" * 80)
print("4. FACTORIAL BREAKDOWN: STRATUM x TARGET RELATION (PRIMARY DATA)")
print("=" * 80)

for model in sorted(primary_df["model_id"].unique()):
    m_df = primary_df[primary_df["model_id"] == model]
    print(f"\n--- Model: {model} ---")
    print(f"{'Stratum':10s} | {'Relation':10s} | {'B0':8s} | {'C1':8s} | {'P1':8s} | {'ΔA (P1-C1)':12s} | {'C4':8s} | {'P4':8s} | {'ΔA (P4-C4)':12s} | n_P1")
    print("-" * 105)
    
    for stratum in ["Unanimous", "Divided"]:
        for relation in ["majority", "minority"]:
            sub = m_df[(m_df["agreement_stratum"] == stratum) & (m_df["target_relation_to_human"] == relation)]
            
            b0 = sub[sub["treatment_id"] == "B0_stripped_baseline"]["is_target_action"].mean()
            c1 = sub[sub["treatment_id"] == "C1_authority_neutral"]["is_target_action"].mean()
            p1 = sub[sub["treatment_id"] == "P1_authority_pressure"]["is_target_action"].mean()
            d_p1 = p1 - c1
            
            c4 = sub[sub["treatment_id"] == "C4_metric_neutral"]["is_target_action"].mean()
            p4 = sub[sub["treatment_id"] == "P4_metric_pressure"]["is_target_action"].mean()
            d_p4 = p4 - c4
            
            n_p1 = len(sub[sub["treatment_id"] == "P1_authority_pressure"])
            
            print(f"{stratum:10s} | {relation:10s} | {b0:8.3f} | {c1:8.3f} | {p1:8.3f} | {d_p1:+12.3f} | {c4:8.3f} | {p4:8.3f} | {d_p4:+12.3f} | {n_p1}")

# 5. MORAL-ACTION DIVERGENCE ANALYSIS
print("\n" + "=" * 80)
print("5. MORAL-ACTION DIVERGENCE (Saying Option A is Right, Recommending Option B)")
print("=" * 80)

div_primary = primary_df[primary_df["divergence"] == 1]
div_all = df[df["divergence"] == 1]

print(f"Primary Divergence Rate: {len(div_primary)}/{len(primary_df)} ({len(div_primary)/len(primary_df)*100:.2f}%)")
print(f"Total Divergence Rate:   {len(div_all)}/{len(df)} ({len(div_all)/len(df)*100:.2f}%)")

print("\n--- Divergence by Treatment × Model (Primary Only) ---")
div_pivot = primary_df.pivot_table(index="treatment_id", columns="model_id", values="divergence", aggfunc=["sum", "mean"])
print(div_pivot.round(4).to_string())

print("\n--- Sample Rationale Traces for Qwen 14B under P1 Authority ---")
qwen_p1_div = primary_df[(primary_df["model_id"] == "qwen3:14b") & (primary_df["treatment_id"] == "P1_authority_pressure") & (primary_df["divergence"] == 1)]
for i, (_, row) in enumerate(qwen_p1_div.head(5).iterrows()):
    print(f"[{i+1}] Scenario {row['scenario_id']} ({row['domain']}, {row['decision_maker_role']}) | Stratum: {row['agreement_stratum']} | Rel: {row['target_relation_to_human']} | Rev: {row['choice_order_reversed']}")
    print(f"    Target: {row['pressure_target_option']}")
    print(f"    Parsed Judgment: {row['parsed_judgment']} (Semantic: {row['semantic_judgment']})")
    print(f"    Parsed Action:   {row['parsed_action']} (Semantic: {row['semantic_action']})")
    print(f"    Rationale: {str(row['parsed_rationale'])[:200]}...")
    print()

print("\n--- Sample Rationale Traces for Gemma 12B under P1 Authority ---")
gemma_p1_div = df[(df["model_id"] == "gemma4:12b") & (df["treatment_id"] == "P1_authority_pressure") & (df["divergence"] == 1)]
for i, (_, row) in enumerate(gemma_p1_div.iterrows()):
    print(f"[{i+1}] Scenario {row['scenario_id']} ({row['domain']}, {row['decision_maker_role']}) | Status: {row['status']} | Rev: {row['choice_order_reversed']}")
    print(f"    Target: {row['pressure_target_option']}")
    print(f"    Parsed Judgment: {row['parsed_judgment']} (Semantic: {row['semantic_judgment']})")
    print(f"    Parsed Action:   {row['parsed_action']} (Semantic: {row['semantic_action']})")
    print(f"    Rationale: {str(row['parsed_rationale'])[:200]}...")
    print()

# 6. DOMAIN BREAKDOWN
print("\n" + "=" * 80)
print("6. DOMAIN-LEVEL ANALYSIS OF AUTHORITY EFFECT (P1 - C1)")
print("=" * 80)

dom_pivot = primary_df.pivot_table(
    index="domain",
    columns=["model_id", "treatment_id"],
    values="is_target_action",
    aggfunc="mean"
)
print(dom_pivot.round(3).to_string())

