"""Read the live JSONL output and run the interim audit."""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

RUN = Path("results/runs/20260809_233031_study_1_production")
reg = pd.read_csv(RUN / "scenario_registry.csv")
plan = pd.read_parquet(RUN / "plan.parquet")

# Read raw JSONL
raw_lines = (RUN / "responses.raw.jsonl").read_text(encoding="utf-8").strip().split("\n")
records = [json.loads(line) for line in raw_lines]
parsed = pd.DataFrame(records)

# Check for exclusions file
excl = pd.DataFrame()
if (RUN / "exclusions.parquet").exists():
    excl = pd.read_parquet(RUN / "exclusions.parquet")
elif (RUN / "exclusions.raw.jsonl").exists():
    excl_lines = (RUN / "exclusions.raw.jsonl").read_text(encoding="utf-8").strip().split("\n")
    excl = pd.DataFrame([json.loads(l) for l in excl_lines]) if excl_lines[0] else pd.DataFrame()

total_done = len(parsed) + len(excl)

print("=" * 80)
print("INTERIM PRODUCTION AUDIT — Study 1 UniMoral (2,304-cell design)")
print("=" * 80)

print(f"\n1. COMPLETION")
print(f"   Planned:    {len(plan)}")
print(f"   Parsed:     {len(parsed)}")
print(f"   Exclusions: {len(excl)}")
print(f"   Done:       {total_done}/{len(plan)} ({total_done/len(plan)*100:.1f}%)")
print(f"   Remaining:  {len(plan) - total_done}")

print(f"\n2. STATUS BREAKDOWN")
print(parsed["status"].value_counts().to_string())

print(f"\n3. MODEL BALANCE")
for m in sorted(parsed["model_id"].unique()):
    n = (parsed["model_id"] == m).sum()
    print(f"   {m}: {n}")

print(f"\n4. SCENARIO COVERAGE")
planned_scen = plan["scenario_id"].nunique()
done_scen = parsed["scenario_id"].nunique()
done_treat = parsed["treatment_id"].nunique()
print(f"   Unique scenarios with data: {done_scen}/{planned_scen}")
print(f"   Unique treatments with data: {done_treat}")

# Merge with registry
df = pd.merge(parsed, reg, on="scenario_id", how="left")

# Semantic choices
def sem(row, col):
    choice = row[col]
    rev = row["choice_order_reversed"]
    if choice == "Option A":
        return "option_b" if rev else "option_a"
    elif choice == "Option B":
        return "option_a" if rev else "option_b"
    return "UNKNOWN"

df["semantic_action"] = df.apply(lambda r: sem(r, "parsed_action"), axis=1)
df["semantic_judgment"] = df.apply(lambda r: sem(r, "parsed_judgment"), axis=1)
df["is_target_action"] = (df["semantic_action"] == df["pressure_target_option"]).astype(int)
df["is_target_judgment"] = (df["semantic_judgment"] == df["pressure_target_option"]).astype(int)
df["divergence"] = (df["semantic_action"] != df["semantic_judgment"]).astype(int)
df["agreement_stratum"] = df["human_entropy"].apply(lambda e: "Unanimous" if e == 0.0 else "Divided")

# Primary only
df_primary = df[df["status"] == "COMPLETED"].copy()

print(f"\n   Primary (direct-valid): {len(df_primary)}")
print(f"   Robustness (retry):    {len(df) - len(df_primary)}")

print(f"\n5. SEMANTIC ORDER STABILITY (primary only)")
nr = df_primary[df_primary["choice_order_reversed"] == False].set_index(["model_id", "scenario_id", "treatment_id"])
rv = df_primary[df_primary["choice_order_reversed"] == True].set_index(["model_id", "scenario_id", "treatment_id"])
common = nr.index.intersection(rv.index)
if len(common) > 0:
    nr_c = nr.loc[common]
    rv_c = rv.loc[common]
    act_match = (nr_c["semantic_action"] == rv_c["semantic_action"]).sum()
    jdg_match = (nr_c["semantic_judgment"] == rv_c["semantic_judgment"]).sum()
    print(f"   Pairs: {len(common)}")
    print(f"   Action agreement:   {act_match}/{len(common)} ({act_match/len(common)*100:.1f}%)")
    print(f"   Judgment agreement: {jdg_match}/{len(common)} ({jdg_match/len(common)*100:.1f}%)")

    for model in sorted(df["model_id"].unique()):
        try:
            m_nr = nr_c.xs(model, level="model_id")
            m_rv = rv_c.xs(model, level="model_id")
            m_act = (m_nr["semantic_action"] == m_rv["semantic_action"]).sum()
            m_jdg = (m_nr["semantic_judgment"] == m_rv["semantic_judgment"]).sum()
            print(f"   {model}: Action={m_act}/{len(m_nr)} ({m_act/len(m_nr)*100:.1f}%), Judgment={m_jdg}/{len(m_nr)} ({m_jdg/len(m_nr)*100:.1f}%)")
        except Exception:
            pass

print(f"\n6. TARGET ACTION RATES BY TREATMENT x MODEL (Primary)")
pivot = df_primary.pivot_table(index="treatment_id", columns="model_id", values="is_target_action", aggfunc="mean")
print(pivot.round(3).to_string())

# Causal deltas
families = {
    "P1_authority_pressure": "C1_authority_neutral",
    "P2_incentive_pressure": "C2_incentive_neutral",
    "P3_social_pressure": "C3_social_neutral",
    "P4_metric_pressure": "C4_metric_neutral",
}

print(f"\n7. CAUSAL DELTAS (ΔA = P_pressure - C_matched)")
for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    print(f"\n   {model}:")
    for p_id, c_id in families.items():
        p_vals = m_df[m_df["treatment_id"] == p_id]["is_target_action"]
        c_vals = m_df[m_df["treatment_id"] == c_id]["is_target_action"]
        if len(p_vals) > 0 and len(c_vals) > 0:
            delta = p_vals.mean() - c_vals.mean()
            print(f"     {p_id:25s}: P={p_vals.mean():.3f} (n={len(p_vals)}) - C={c_vals.mean():.3f} (n={len(c_vals)}) = ΔA={delta:+.3f}")

print(f"\n8. AUTHORITY BY STRATUM x RELATION (Primary)")
for model in sorted(df_primary["model_id"].unique()):
    m_df = df_primary[df_primary["model_id"] == model]
    print(f"\n   {model}:")
    for stratum in ["Unanimous", "Divided"]:
        for relation in ["majority", "minority"]:
            s_df = m_df[(m_df["agreement_stratum"] == stratum) & (m_df["target_relation_to_human"] == relation)]
            b0 = s_df[s_df["treatment_id"] == "B0_stripped_baseline"]["is_target_action"].mean()
            c1 = s_df[s_df["treatment_id"] == "C1_authority_neutral"]["is_target_action"].mean()
            p1 = s_df[s_df["treatment_id"] == "P1_authority_pressure"]["is_target_action"].mean()
            n_p1 = len(s_df[s_df["treatment_id"] == "P1_authority_pressure"])
            delta = p1 - c1 if not (np.isnan(p1) or np.isnan(c1)) else float("nan")
            print(f"     {stratum:10s} x {relation:8s}: B0={b0:.3f}, C1={c1:.3f}, P1={p1:.3f} (n={n_p1}) -> dA={delta:+.3f}")

print(f"\n9. DIVERGENCE (Action != Judgment) — Primary Only")
div_p = df_primary[df_primary["divergence"] == 1]
print(f"   Total: {len(div_p)}/{len(df_primary)} ({len(div_p)/len(df_primary)*100:.1f}%)")
if len(div_p) > 0:
    print(f"\n   By Treatment x Model:")
    cross = div_p.groupby(["model_id", "treatment_id"]).size()
    print(cross.to_string())

# Save interim CSV
df.to_csv(RUN / "interim_results.csv", index=False)
print(f"\n10. EXPORTED: interim_results.csv ({len(df)} rows)")
