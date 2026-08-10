"""
Comprehensive analysis script for Study 1 UniMoral Validation Run (216 cells).
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

RUN_DIR = Path("results/runs/20260809_214130_study1_unimoral_validation")

# Load data
plan_df = pd.read_parquet(RUN_DIR / "plan.parquet")
parsed_df = pd.read_parquet(RUN_DIR / "responses.parsed.parquet")
excl_df = pd.read_parquet(RUN_DIR / "exclusions.parquet")
registry_df = pd.read_csv(RUN_DIR / "scenario_registry.csv")

print("=" * 80)
print("1. OVERALL EXECUTION & COMPLETION SUMMARY")
print("=" * 80)
print(f"Total planned cells: {len(plan_df)}")
print(f"Total parsed responses: {len(parsed_df)}")
print(f"Total exclusions: {len(excl_df)}")

# Join parsed with registry to get scenario metadata
df = pd.merge(parsed_df, registry_df, on="scenario_id", how="left")

print(f"Merged records: {len(df)}")
print(f"Models: {df['model_id'].unique()}")
print(f"Treatments: {df['treatment_id'].unique()}")
print(f"Scenarios: {df['scenario_id'].unique()}")

# Check status distribution
print("\n--- Parsing / Retry Status ---")
print(df["status"].value_counts())

# Check exclusion details
print("\n--- Exclusions ---")
print(excl_df["status"].value_counts())

print("\n" + "=" * 80)
print("2. SEMANTIC ORDER ROBUSTNESS (Option Order Counterbalancing)")
print("=" * 80)

# Compare choice_order_reversed=False vs True for identical (model, scenario, treatment)
non_rev = df[df["choice_order_reversed"] == False].set_index(["model_id", "scenario_id", "treatment_id"])
rev = df[df["choice_order_reversed"] == True].set_index(["model_id", "scenario_id", "treatment_id"])

common_idx = non_rev.index.intersection(rev.index)
print(f"Pairs compared: {len(common_idx)}")

# Determine if the semantic choice matches
# When reversed=False: Option A = semantic_a, Option B = semantic_b
# When reversed=True: Option A = semantic_b, Option B = semantic_a
# So semantic judgment: if non_rev chose Option A, it chose option_a. If rev chose Option B, it chose option_a.
def get_semantic_choice(row):
    choice = row["parsed_action"]  # "Option A" or "Option B"
    is_rev = row["choice_order_reversed"]
    if choice == "Option A":
        return "option_b" if is_rev else "option_a"
    elif choice == "Option B":
        return "option_a" if is_rev else "option_b"
    return "UNKNOWN"

def get_semantic_judgment(row):
    choice = row["parsed_judgment"]
    is_rev = row["choice_order_reversed"]
    if choice == "Option A":
        return "option_b" if is_rev else "option_a"
    elif choice == "Option B":
        return "option_a" if is_rev else "option_b"
    return "UNKNOWN"

df["semantic_action"] = df.apply(get_semantic_choice, axis=1)
df["semantic_judgment"] = df.apply(get_semantic_judgment, axis=1)
df["is_target_action"] = (df["semantic_action"] == df["pressure_target_option"]).astype(int)
df["is_target_judgment"] = (df["semantic_judgment"] == df["pressure_target_option"]).astype(int)
df["divergence"] = (df["semantic_action"] != df["semantic_judgment"]).astype(int)

# Re-slice for counterbalancing comparison
df_nr = df[df["choice_order_reversed"] == False].set_index(["model_id", "scenario_id", "treatment_id"])
df_r = df[df["choice_order_reversed"] == True].set_index(["model_id", "scenario_id", "treatment_id"])

common_idx = df_nr.index.intersection(df_r.index)
df_nr = df_nr.loc[common_idx]
df_r = df_r.loc[common_idx]

match_action = (df_nr["semantic_action"] == df_r["semantic_action"]).sum()
match_judgment = (df_nr["semantic_judgment"] == df_r["semantic_judgment"]).sum()
total_pairs = len(common_idx)

print(f"Action semantic agreement across order reversal: {match_action}/{total_pairs} ({match_action/total_pairs*100:.1f}%)")
print(f"Judgment semantic agreement across order reversal: {match_judgment}/{total_pairs} ({match_judgment/total_pairs*100:.1f}%)")

# Break down order agreement by model
for model in df["model_id"].unique():
    m_nr = df_nr.xs(model, level="model_id")
    m_r = df_r.xs(model, level="model_id")
    m_action_match = (m_nr["semantic_action"] == m_r["semantic_action"]).sum()
    m_judg_match = (m_nr["semantic_judgment"] == m_r["semantic_judgment"]).sum()
    print(f"  {model}: Action agreement = {m_action_match}/{len(m_nr)} ({m_action_match/len(m_nr)*100:.1f}%), Judgment agreement = {m_judg_match}/{len(m_nr)} ({m_judg_match/len(m_nr)*100:.1f}%)")

print("\n" + "=" * 80)
print("3. TREATMENT EFFECTS: TARGET SELECTION RATES")
print("=" * 80)

# Target action rate by treatment & model
pivot_action = df.pivot_table(index="treatment_id", columns="model_id", values="is_target_action", aggfunc="mean")
pivot_judg = df.pivot_table(index="treatment_id", columns="model_id", values="is_target_judgment", aggfunc="mean")

print("\n--- Target Action Compliance Rate (P_target_action) ---")
print(pivot_action.round(3))

print("\n--- Target Judgment Compliance Rate (P_target_judgment) ---")
print(pivot_judg.round(3))

# Divergence (Action != Judgment)
pivot_div = df.pivot_table(index="treatment_id", columns="model_id", values="divergence", aggfunc=["mean", "sum"])
print("\n--- Divergence Rate (Action != Judgment) ---")
print(pivot_div.round(3))

print("\n" + "=" * 80)
print("4. STRATUM & RELATION BREAKDOWNS")
print("=" * 80)

# Stratum: Unanimous (3/3) vs Divided (2/1)
df["agreement_stratum"] = df["human_entropy"].apply(lambda e: "Unanimous (3/3)" if e == 0.0 else "Divided (2/1)")

print("\n--- Target Action Rate by Model x Stratum x Treatment ---")
strat_pivot = df.pivot_table(
    index=["treatment_id"],
    columns=["model_id", "agreement_stratum"],
    values="is_target_action",
    aggfunc="mean"
)
print(strat_pivot.round(3))

print("\n--- Target Action Rate by Model x Target Relation (majority vs minority) x Treatment ---")
rel_pivot = df.pivot_table(
    index=["treatment_id"],
    columns=["model_id", "target_relation_to_human"],
    values="is_target_action",
    aggfunc="mean"
)
print(rel_pivot.round(3))

print("\n" + "=" * 80)
print("5. MATCHED CONTROLS VS BASELINE (B0)")
print("=" * 80)

b0_act = df[df["treatment_id"] == "B0_stripped_baseline"].groupby("model_id")["is_target_action"].mean()
print(f"B0 Target Action Rate:\n{b0_act.round(3)}")

controls = ["C1_authority_neutral", "C2_incentive_neutral", "C3_social_neutral", "C4_metric_neutral"]
ctrl_act = df[df["treatment_id"].isin(controls)].groupby(["treatment_id", "model_id"])["is_target_action"].mean().unstack()
print(f"\nNeutral Control Target Action Rates:\n{ctrl_act.round(3)}")

print("\n" + "=" * 80)
print("6. DIVERGENCE CASES (Saying it's wrong, recommending doing it anyway)")
print("=" * 80)

div_cases = df[df["divergence"] == 1]
print(f"Total divergence instances: {len(div_cases)} out of {len(df)} ({len(div_cases)/len(df)*100:.1f}%)")
print("\nDivergence by Model x Treatment:")
print(div_cases.groupby(["model_id", "treatment_id"]).size().unstack(fill_value=0))

if len(div_cases) > 0:
    print("\nSample Divergence Instances:")
    for _, row in div_cases.head(10).iterrows():
        print(f"  [{row['model_id']}] Scenario: {row['scenario_id']} | Treatment: {row['treatment_id']} | Reversed: {row['choice_order_reversed']}")
        print(f"    Target: {row['pressure_target_option']}")
        print(f"    Judgment: {row['parsed_judgment']} (Semantic: {row['semantic_judgment']})")
        print(f"    Action:   {row['parsed_action']} (Semantic: {row['semantic_action']})")
        print(f"    Rationale: {str(row['parsed_rationale'])[:150]}...")
        print()

print("\n" + "=" * 80)
print("7. SCENARIO-LEVEL BREAKDOWN")
print("=" * 80)

scen_pivot = df.pivot_table(
    index=["scenario_id", "domain", "decision_maker_role", "agreement_stratum", "target_relation_to_human"],
    columns=["model_id", "treatment_id"],
    values="is_target_action",
    aggfunc="mean"
)
print(scen_pivot.to_string())

