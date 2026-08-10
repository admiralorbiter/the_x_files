"""
Profile UniMoral English data from cached HuggingFace CSVs.
Loads English long + short formatted files, aggregates per-annotator choices,
and computes entropy distributions for IMPACT scenario selection.
"""
import pandas as pd
import math
import json
from pathlib import Path
from collections import defaultdict

HF_CACHE = Path.home() / ".cache/huggingface/hub/datasets--shivaniku--UniMoral/snapshots/d74cd5140261a58456727606f10ea31de06365e8"

def calc_entropy(p_a, p_b):
    if p_a <= 0.0 or p_a >= 1.0:
        return 0.0
    return -(p_a * math.log2(p_a) + p_b * math.log2(p_b))

# Load English CSVs
files = [
    HF_CACHE / "English_long_formatted.csv",
    HF_CACHE / "English_short_formatted.csv",
]

dfs = []
for f in files:
    print(f"Loading {f.name}...")
    df = pd.read_csv(f)
    df["source_file"] = f.name
    dfs.append(df)
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")

df_all = pd.concat(dfs, ignore_index=True)
print(f"\nTotal English rows: {len(df_all)}")
print(f"Columns: {list(df_all.columns)}")

# Show first record
print("\n=== FIRST RECORD ===")
for col in df_all.columns:
    val = str(df_all.iloc[0][col])
    if len(val) > 300:
        val = val[:300] + "..."
    print(f"  {col}: {val}")

# Identify key fields
print("\n=== UNIQUE SCENARIO_IDS ===")
if "Scenario_id" in df_all.columns:
    scen_col = "Scenario_id"
elif "scenario_id" in df_all.columns:
    scen_col = "scenario_id"
else:
    # Try to find scenario column
    for c in df_all.columns:
        if "scenario" in c.lower() or "dilemma" in c.lower():
            scen_col = c
            break
    else:
        print("ERROR: No scenario ID column found")
        print("Available columns:", list(df_all.columns))
        exit(1)

print(f"  Scenario column: {scen_col}")
unique_scenarios = df_all[scen_col].nunique()
print(f"  Unique scenarios: {unique_scenarios}")

# Find action columns
action_cols = [c for c in df_all.columns if "action" in c.lower()]
print(f"\n  Action-related columns: {action_cols}")

# Find the Possible_actions and Selected_action columns
possible_col = None
selected_col = None
for c in df_all.columns:
    cl = c.lower()
    if "possible" in cl and "action" in cl:
        possible_col = c
    if "selected" in cl and "action" in cl:
        selected_col = c

print(f"  Possible actions column: {possible_col}")
print(f"  Selected action column: {selected_col}")

# Find annotator column
annotator_col = None
for c in df_all.columns:
    if "annotator" in c.lower() and "id" in c.lower():
        annotator_col = c
        break

print(f"  Annotator column: {annotator_col}")

# Aggregate per scenario
print("\n=== AGGREGATING PER-SCENARIO STATISTICS ===")
scenario_stats = defaultdict(lambda: {
    "count": 0,
    "actions": [],
    "scenario_text": "",
    "possible_actions_raw": "",
    "source_file": "",
})

for _, row in df_all.iterrows():
    sid = row[scen_col]
    stats = scenario_stats[sid]
    stats["count"] += 1
    if selected_col:
        stats["actions"].append(row[selected_col])
    if possible_col and not stats["possible_actions_raw"]:
        stats["possible_actions_raw"] = str(row[possible_col])
    # Try to capture scenario text
    for c in df_all.columns:
        cl = c.lower()
        if ("dilemma" in cl or "scenario" in cl or "situation" in cl) and "id" not in cl and not stats["scenario_text"]:
            val = str(row[c])
            if len(val) > 30:
                stats["scenario_text"] = val
    stats["source_file"] = row["source_file"]

# Compute entropy
scenario_list = []
for sid, stats in scenario_stats.items():
    n = stats["count"]
    if n < 3:
        continue
    
    # Count action selections
    action_counter = defaultdict(int)
    for a in stats["actions"]:
        action_counter[str(a)] += 1
    
    # If binary (2 actions), compute entropy
    action_keys = sorted(action_counter.keys())
    if len(action_keys) == 2:
        count_a = action_counter[action_keys[0]]
        count_b = action_counter[action_keys[1]]
        p_a = count_a / n
        p_b = count_b / n
        entropy = calc_entropy(p_a, p_b)
    elif len(action_keys) == 1:
        entropy = 0.0
        count_a = n
        count_b = 0
        p_a = 1.0
        p_b = 0.0
    else:
        # More than 2 actions - skip for now
        continue
    
    scenario_list.append({
        "scenario_id": sid,
        "n": n,
        "action_counts": dict(action_counter),
        "p_a": round(p_a, 4),
        "p_b": round(p_b, 4),
        "entropy": round(entropy, 6),
        "possible_actions_raw": stats["possible_actions_raw"][:500],
        "scenario_text": stats["scenario_text"][:500],
        "source_file": stats["source_file"],
    })

print(f"Scenarios with >= 3 annotators and binary choices: {len(scenario_list)}")

# Entropy distribution
if scenario_list:
    entropies = [s["entropy"] for s in scenario_list]
    ns = [s["n"] for s in scenario_list]
    print(f"  Entropy range: {min(entropies):.4f} - {max(entropies):.4f}")
    print(f"  Mean entropy: {sum(entropies)/len(entropies):.4f}")
    print(f"  Annotator count range: {min(ns)} - {max(ns)}")
    print(f"  Mean n: {sum(ns)/len(ns):.1f}")
    print(f"  Median n: {sorted(ns)[len(ns)//2]}")
    
    # Tier distribution
    high = [s for s in scenario_list if s["entropy"] >= 0.85]
    mid = [s for s in scenario_list if 0.65 <= s["entropy"] < 0.85]
    low = [s for s in scenario_list if s["entropy"] < 0.65]
    print(f"\n  Entropy tiers:")
    print(f"    High (>= 0.85): {len(high)}")
    print(f"    Mid (0.65-0.85): {len(mid)}")
    print(f"    Low (< 0.65): {len(low)}")
    
    # Show 15 sample scenarios across entropy range
    sorted_scenarios = sorted(scenario_list, key=lambda x: x["entropy"])
    sample_indices = [0, len(sorted_scenarios)//4, len(sorted_scenarios)//2, 3*len(sorted_scenarios)//4, -1]
    
    print("\n=== SAMPLE SCENARIOS ACROSS ENTROPY RANGE ===")
    for idx in sample_indices:
        s = sorted_scenarios[idx]
        print(f"\n  [{s['scenario_id']}] H={s['entropy']:.3f} n={s['n']}")
        print(f"    Actions: {s['action_counts']}")
        print(f"    Possible: {s['possible_actions_raw'][:200]}")
        print(f"    Scenario: {s['scenario_text'][:200]}")

# Save for further analysis
out_dir = Path("data/raw/unimoral")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "english_scenario_profiles.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(scenario_list, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(scenario_list)} scenario profiles to {out_path}")
