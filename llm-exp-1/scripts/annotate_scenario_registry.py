"""
Annotate Scenario Registry for IMPACT Study 1.

Parses source_item_id to extract:
- moral_framework (DIT, MJI, MCT, REDDIT, OTHER)
- moral_factor (Rules, Legality, Responsibilities, Emotions, Culture, Relationships, Sacred Values, Politeness, Moral, etc.)
- factor_group (rule_duty_tagged vs other_factor_tagged)
- merges curated label_collision and role_mismatch flags from data/curated/study_1_scenario_audit.csv
"""

import pandas as pd
import re
from pathlib import Path

RUN = Path("results/runs/20260809_233031_study_1_production")
registry_path = RUN / "scenario_registry.csv"
audit_path = Path("data/curated/study_1_scenario_audit.csv")

df = pd.read_csv(registry_path)
audit_df = pd.read_csv(audit_path)

def parse_source_tag(source_id):
    if pd.isna(source_id):
        return "UNKNOWN", "UNKNOWN"
    source_str = str(source_id)
    
    if "Reddit" in source_str:
        return "REDDIT", "Reddit_Anecdote"
        
    match = re.search(r'_(DIT|MJI|MCT)_(.+)$', source_str)
    if match:
        framework, factor = match.group(1), match.group(2)
        return framework, factor
        
    return "OTHER", "Unclassified"

frameworks = []
factors = []
groups = []

RULE_DUTY_FACTORS = {"Rules", "Legality", "Responsibilities"}

for _, row in df.iterrows():
    fw, fac = parse_source_tag(row.get("source_item_id"))
    frameworks.append(fw)
    factors.append(fac)
    
    # Exploratory source-factor proxy. These are UniMoral source annotation tags,
    # not independently validated normative-anchor classifications.
    if fac in RULE_DUTY_FACTORS:
        groups.append("rule_duty_tagged")
    else:
        groups.append("other_factor_tagged")

df["moral_framework"] = frameworks
df["moral_factor"] = factors
df["factor_group"] = groups

# Merge curated audit annotations
df = df.merge(
    audit_df[["scenario_id", "label_collision", "role_mismatch", "audit_note"]],
    on="scenario_id",
    how="left"
)
df["label_collision"] = df["label_collision"].fillna(0).astype(int)
df["role_mismatch"] = df["role_mismatch"].fillna(0).astype(int)

output_path = RUN / "scenario_registry_annotated.csv"
df.to_csv(output_path, index=False)

print(f"Successfully annotated scenario registry.")
print(f"Saved to: {output_path}")
print("\n--- Factor Group Distribution ---")
print(df["factor_group"].value_counts().to_string())
print("\n--- Moral Factor Distribution ---")
print(df["moral_factor"].value_counts().to_string())
print("\n--- Curated Scenario Audit Flags ---")
print(f"Label Collisions: {df['label_collision'].sum()}")
print(f"Role Mismatches:  {df['role_mismatch'].sum()}")
