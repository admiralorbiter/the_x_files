"""
Data completeness audit for Study 1 production run.
Checks whether we have all the data we need before analysis.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

RUN = Path("results/runs/20260809_233031_study_1_production")
plan = pd.read_parquet(RUN / "plan.parquet")
parsed = pd.read_parquet(RUN / "responses.parsed.parquet")
excl = pd.read_parquet(RUN / "exclusions.parquet") if (RUN / "exclusions.parquet").exists() else pd.DataFrame()
reg = pd.read_csv(RUN / "scenario_registry.csv")

print("=" * 80)
print("DATA COMPLETENESS AUDIT — Study 1 Production Run")
print("=" * 80)

# 1. OVERALL COMPLETION
total_done = len(parsed) + len(excl)
print(f"\n1. OVERALL COMPLETION")
print(f"   Planned cells:  {len(plan)}")
print(f"   Parsed:         {len(parsed)}")
print(f"   Excluded:       {len(excl)}")
print(f"   Total accounted: {total_done} / {len(plan)} ({total_done/len(plan)*100:.2f}%)")
print(f"   UNACCOUNTED:    {len(plan) - total_done}")

# Check if any planned cells are completely missing (not in parsed OR excluded)
parsed_ids = set(parsed["cell_id"].tolist())
excl_ids = set(excl["cell_id"].tolist()) if len(excl) > 0 else set()
plan_ids = set(plan["cell_id"].tolist())
missing_ids = plan_ids - parsed_ids - excl_ids

if missing_ids:
    print(f"\n   *** WARNING: {len(missing_ids)} planned cells have NO response at all ***")
    missing_plan = plan[plan["cell_id"].isin(missing_ids)]
    print(f"   Missing by model:")
    print(missing_plan["model_id"].value_counts().to_string())
    print(f"   Missing by treatment:")
    print(missing_plan["treatment_id"].value_counts().to_string())
else:
    print(f"\n   ✓ All planned cells are accounted for (parsed or excluded).")

# 2. STATUS BREAKDOWN
print(f"\n2. STATUS BREAKDOWN")
print(f"   Direct valid (COMPLETED):       {(parsed['status'] == 'COMPLETED').sum()}")
print(f"   Format retry success:           {(parsed['status'] == 'FORMAT_RETRY_SUCCESS').sum()}")
if 'SERVER_ERROR' in parsed['status'].values:
    print(f"   Server errors (in parsed):      {(parsed['status'] == 'SERVER_ERROR').sum()}")
print(f"   Excluded (FORMAT_FAILED/other): {len(excl)}")
if len(excl) > 0:
    print(f"   Exclusion statuses: {excl['status'].value_counts().to_dict()}")

# 3. MISSING CELLS ANALYSIS
print(f"\n3. MISSING/EXCLUDED CELLS ANALYSIS")
if len(excl) > 0:
    excl_merged = pd.merge(excl, reg, on="scenario_id", how="left")
    print(f"   Total excluded cells: {len(excl)}")
    print(f"\n   By model:")
    print(excl["model_id"].value_counts().to_string())
    print(f"\n   By treatment:")
    print(excl["treatment_id"].value_counts().to_string())
    print(f"\n   By target relation:")
    if "target_relation_to_human" in excl_merged.columns:
        print(excl_merged["target_relation_to_human"].value_counts().to_string())
    print(f"\n   Individual excluded cells:")
    for _, row in excl_merged.iterrows():
        rev = row.get("choice_order_reversed", "?")
        rel = row.get("target_relation_to_human", "?")
        strat = "Unanimous" if row.get("human_entropy", 1) == 0 else "Divided"
        print(f"     {row['model_id']:12s} | {row['scenario_id']:15s} | {row['treatment_id']:25s} | rev={rev} | {rel} | {strat}")
else:
    print("   No excluded cells.")

# 4. FACTORIAL CELL COMPLETENESS
print(f"\n4. FACTORIAL CELL COMPLETENESS")
print(f"   Checking if every (scenario × treatment × model × order) cell has data...")

# Merge parsed with plan to check
parsed_keys = set(zip(parsed["scenario_id"], parsed["treatment_id"], parsed["model_id"], parsed["choice_order_reversed"]))
plan_keys = set(zip(plan["scenario_id"], plan["treatment_id"], plan["model_id"], plan["choice_order_reversed"]))

missing_keys = plan_keys - parsed_keys
if missing_keys:
    print(f"   {len(missing_keys)} cells missing from parsed responses.")
    # Group by model
    by_model = defaultdict(int)
    by_treat = defaultdict(int)
    for s, t, m, o in missing_keys:
        by_model[m] += 1
        by_treat[t] += 1
    print(f"   Missing by model: {dict(by_model)}")
    print(f"   Missing by treatment: {dict(by_treat)}")
else:
    print(f"   ✓ All factorial cells have parsed responses.")

# 5. COUNTERBALANCING PAIR COMPLETENESS
print(f"\n5. COUNTERBALANCING PAIR COMPLETENESS")
print(f"   Checking if every (scenario × treatment × model) has BOTH order variants...")

primary = parsed[parsed["status"] == "COMPLETED"]
groups = primary.groupby(["scenario_id", "treatment_id", "model_id"])["choice_order_reversed"].apply(set)
complete_pairs = sum(1 for s in groups if s == {True, False})
incomplete_pairs = sum(1 for s in groups if s != {True, False})
total_groups = len(groups)

print(f"   Total (scenario × treatment × model) groups: {total_groups}")
print(f"   Complete pairs (both orders, primary): {complete_pairs}")
print(f"   Incomplete pairs (missing one order): {incomplete_pairs}")

if incomplete_pairs > 0:
    incomplete = [(idx, s) for idx, s in groups.items() if s != {True, False}]
    print(f"\n   Incomplete pair details:")
    for (scen, treat, model), orders in incomplete[:20]:
        print(f"     {model:12s} | {scen:15s} | {treat:25s} | has_orders={orders}")

# 6. DESIGN BALANCE CHECK ON AVAILABLE DATA
print(f"\n6. DESIGN BALANCE ON AVAILABLE PRIMARY DATA")
primary_merged = pd.merge(primary, reg, on="scenario_id", how="left")
primary_merged["agreement_stratum"] = primary_merged["human_entropy"].apply(lambda e: "Unanimous" if e == 0.0 else "Divided")

for model in sorted(primary_merged["model_id"].unique()):
    m_df = primary_merged[primary_merged["model_id"] == model]
    print(f"\n   {model}:")
    
    # Check balance per treatment
    for treat in sorted(m_df["treatment_id"].unique()):
        t_df = m_df[m_df["treatment_id"] == treat]
        n = len(t_df)
        n_unan = (t_df["agreement_stratum"] == "Unanimous").sum()
        n_div = (t_df["agreement_stratum"] == "Divided").sum()
        n_maj = (t_df["target_relation_to_human"] == "majority").sum()
        n_min = (t_df["target_relation_to_human"] == "minority").sum()
        
        balance_ok = "✓" if n_unan == n_div and n_maj == n_min else "⚠"
        print(f"     {treat:25s}: n={n:3d} | Unan/Div={n_unan}/{n_div} | Maj/Min={n_maj}/{n_min} {balance_ok}")

# 7. CAN WE DO MATCHED PAIRED ANALYSIS?
print(f"\n7. MATCHED PAIRED ANALYSIS FEASIBILITY")
families = {
    "P1_authority_pressure": "C1_authority_neutral",
    "P2_incentive_pressure": "C2_incentive_neutral",
    "P3_social_pressure": "C3_social_neutral",
    "P4_metric_pressure": "C4_metric_neutral",
}

for model in sorted(primary_merged["model_id"].unique()):
    m_df = primary_merged[primary_merged["model_id"] == model]
    print(f"\n   {model}:")
    
    for p_id, c_id in families.items():
        p_keys = set(zip(
            m_df[m_df["treatment_id"] == p_id]["scenario_id"],
            m_df[m_df["treatment_id"] == p_id]["choice_order_reversed"]
        ))
        c_keys = set(zip(
            m_df[m_df["treatment_id"] == c_id]["scenario_id"],
            m_df[m_df["treatment_id"] == c_id]["choice_order_reversed"]
        ))
        matched = p_keys & c_keys
        p_only = p_keys - c_keys
        c_only = c_keys - p_keys
        
        status = "✓" if len(p_only) == 0 and len(c_only) == 0 else "⚠ PARTIAL"
        print(f"     {p_id:25s} vs {c_id:25s}: matched={len(matched)}, P-only={len(p_only)}, C-only={len(c_only)} {status}")

print(f"\n{'='*80}")
print(f"VERDICT")
print(f"{'='*80}")
