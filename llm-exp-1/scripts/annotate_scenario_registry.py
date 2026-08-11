"""
Annotate Scenario Registry for IMPACT Study 1.

Parses source_item_id to extract:
- moral_framework (DIT, MJI, MCT, REDDIT, OTHER)
- moral_factor (Rules, Legality, Responsibilities, Emotions, Culture, Relationships, Sacred Values, Politeness, Moral, etc.)
- factor_group (rule_anchored vs tradeoff)
- label_collision flag (scenarios unimoral_003, unimoral_004, unimoral_043)
- role_mismatch flag (scenarios unimoral_009, unimoral_056)
"""

import pandas as pd
import re
from pathlib import Path

RUN = Path("results/runs/20260809_233031_study_1_production")
registry_path = RUN / "scenario_registry.csv"

df = pd.read_csv(registry_path)

def parse_source_tag(source_id):
    if pd.isna(source_id):
        return "UNKNOWN", "UNKNOWN"
    source_str = str(source_id)
    
    if "Reddit" in source_str:
        return "REDDIT", "Reddit_Anecdote"
        
    # Match pattern like short_id_79_DIT_Culture or long_id_4_MJI_Emotions
    match = re.search(r'_(DIT|MJI|MCT)_(.+)$', source_str)
    if match:
        framework, factor = match.group(1), match.group(2)
        return framework, factor
        
    return "OTHER", "Unclassified"

frameworks = []
factors = []
groups = []
label_collisions = []
role_mismatches = []

RULE_DUTY_FACTORS = {"Rules", "Legality", "Responsibilities"}

for _, row in df.iterrows():
    s_id = row["scenario_id"]
    fw, fac = parse_source_tag(row.get("source_item_id"))
    frameworks.append(fw)
    factors.append(fac)
    
    # Exploratory source-factor proxy. These are UniMoral source annotation tags,
    # not independently validated normative-anchor classifications.
    if fac in RULE_DUTY_FACTORS:
        groups.append("rule_duty_tagged")
    else:
        groups.append("tradeoff")
        
    # Known label collisions
    if s_id in {"unimoral_003", "unimoral_004", "unimoral_043"}:
        label_collisions.append(1)
    else:
        label_collisions.append(0)
        
    # Known role mismatches
    if s_id in {"unimoral_009", "unimoral_056"}:
        role_mismatches.append(1)
    else:
        role_mismatches.append(0)

df["moral_framework"] = frameworks
df["moral_factor"] = factors
df["factor_group"] = groups
df["label_collision"] = label_collisions
df["role_mismatch"] = role_mismatches

output_path = RUN / "scenario_registry_annotated.csv"
df.to_csv(output_path, index=False)

print(f"Successfully annotated scenario registry.")
print(f"Saved to: {output_path}")
print("\n--- Factor Group Distribution ---")
print(df["factor_group"].value_counts().to_string())
print("\n--- Moral Factor Distribution ---")
print(df["moral_factor"].value_counts().to_string())
