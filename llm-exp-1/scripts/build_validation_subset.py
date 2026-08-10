"""
Build the 6-scenario validation subset from the 64-scenario production corpus.

Selection criteria (from reviewer):
- 1 unanimous + majority-target
- 1 unanimous + minority-target  
- 1 divided + majority-target
- 1 divided + minority-target
- 2 additional for A/B target balance + domain diversity
- At least 3 different institutional domains
"""
import json
from pathlib import Path

with open("data/curated/production_scenarios.json", "r", encoding="utf-8") as f:
    all_scenarios = json.load(f)

# Build lookup by design cell
cells = {}
for s in all_scenarios:
    agreement = "unanimous" if s["human_entropy"] == 0.0 else "divided"
    key = (agreement, s["target_relation_to_human"], s["pressure_target_option"])
    if key not in cells:
        cells[key] = []
    cells[key].append(s)

# Pick 6 with domain diversity and A/B balance
selected = []
used_domains = set()

# 1. Unanimous + majority + option_a (pick a non-Healthcare domain if possible)
for s in cells[("unanimous", "majority", "option_a")]:
    if s["domain"] not in used_domains and s["domain"] != "Healthcare":
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("unanimous", "majority", "option_a")][0])
    used_domains.add(cells[("unanimous", "majority", "option_a")][0]["domain"])

# 2. Unanimous + minority + option_b
for s in cells[("unanimous", "minority", "option_b")]:
    if s["domain"] not in used_domains:
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("unanimous", "minority", "option_b")][0])
    used_domains.add(cells[("unanimous", "minority", "option_b")][0]["domain"])

# 3. Divided + majority + option_b
for s in cells[("divided", "majority", "option_b")]:
    if s["domain"] not in used_domains:
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("divided", "majority", "option_b")][0])
    used_domains.add(cells[("divided", "majority", "option_b")][0]["domain"])

# 4. Divided + minority + option_a
for s in cells[("divided", "minority", "option_a")]:
    if s["domain"] not in used_domains:
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("divided", "minority", "option_a")][0])
    used_domains.add(cells[("divided", "minority", "option_a")][0]["domain"])

# 5. Additional unanimous + majority + option_b (new domain)
for s in cells[("unanimous", "majority", "option_b")]:
    if s["domain"] not in used_domains:
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("unanimous", "majority", "option_b")][0])

# 6. Additional divided + minority + option_b (new domain)
for s in cells[("divided", "minority", "option_b")]:
    if s["domain"] not in used_domains:
        selected.append(s)
        used_domains.add(s["domain"])
        break
else:
    selected.append(cells[("divided", "minority", "option_b")][0])

# Audit
print(f"Selected {len(selected)} validation scenarios:")
print()
target_a = sum(1 for s in selected if s["pressure_target_option"] == "option_a")
target_b = sum(1 for s in selected if s["pressure_target_option"] == "option_b")
maj = sum(1 for s in selected if s["target_relation_to_human"] == "majority")
mino = sum(1 for s in selected if s["target_relation_to_human"] == "minority")
unan = sum(1 for s in selected if s["human_entropy"] == 0.0)
div = sum(1 for s in selected if s["human_entropy"] > 0.0)

for s in selected:
    agreement = "UNANIMOUS" if s["human_entropy"] == 0.0 else "DIVIDED"
    print(f"  {s['scenario_id']} | {agreement} | {s['target_relation_to_human']} | {s['pressure_target_option']} | {s['domain']} | {s['decision_maker_role']}")

print(f"\nBalance: target_a={target_a} target_b={target_b} | majority={maj} minority={mino} | unanimous={unan} divided={div}")
print(f"Domains: {used_domains}")
print(f"Expected cells: 6 x 9 treatments x 2 models x 2 orders = {6*9*2*2}")

# Save validation subset
out_path = Path("data/curated/validation_scenarios.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {out_path}")
