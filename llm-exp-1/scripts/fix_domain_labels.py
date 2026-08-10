"""Apply domain label fixes to production_scenarios.json and validation_scenarios.json."""
import json
from pathlib import Path

FIXES = {
    "unimoral_003": "Corporate/Workplace",
    "unimoral_026": "Media/Journalism",    # Keep — scenario IS about a journalist
    "unimoral_031": "Corporate/Workplace",
    "unimoral_036": "Corporate/Workplace",
    "unimoral_049": "Media/Journalism",    # Keep — actor IS a journalist covering govt corruption
    "unimoral_050": "Corporate/Workplace",
    "unimoral_051": "Corporate/Workplace",
    "unimoral_052": "Media/Journalism",    # Keep — actor IS a journalist covering govt corruption
    "unimoral_056": "Military",
    "unimoral_064": "Government",
}

# Let me re-check each suggested fix manually by reading the scenarios
with open("data/curated/production_scenarios.json", "r", encoding="utf-8") as f:
    scenarios = json.load(f)

# Manual review of each fix
for s in scenarios:
    if s["scenario_id"] in FIXES:
        old = s["domain"]
        # For journalist scenarios covering government: the actor is a journalist, domain should be Media/Journalism
        # For corporate scenarios mislabeled as Military: fix to Corporate/Workplace
        # For government official scenarios: fix to Government
        kernel = s["ethical_kernel"][:200]
        print(f"{s['scenario_id']}: {old} -> {FIXES[s['scenario_id']]}")
        print(f"  Role: {s['decision_maker_role']}")
        print(f"  Kernel: {kernel}")
        print()

# Now let me be more careful with the journalist ones
# unimoral_026: "A journalist has uncovered..." — domain should stay Media/Journalism, not Corporate/Workplace
# unimoral_049: "A journalist has uncovered a corruption scandal..." — Media/Journalism is correct
# unimoral_052: "A journalist has discovered a corruption scandal..." — Media/Journalism is correct

# Revised fixes after manual review
FINAL_FIXES = {
    "unimoral_003": "Corporate/Workplace",  # Manager scenario mislabeled
    # unimoral_026: already Media/Journalism — skip if correct
    "unimoral_031": "Corporate/Workplace",  # CEO/company scenario mislabeled as Military
    "unimoral_036": "Corporate/Workplace",  # Manager/employee scenario mislabeled as Military
    # unimoral_049: keep as Media/Journalism — journalist is the actor
    "unimoral_050": "Corporate/Workplace",  # "Alex discovered company illegal practices" — Legal -> Corporate
    "unimoral_051": "Corporate/Workplace",  # Company layoffs mislabeled as Military
    # unimoral_052: keep as Media/Journalism — journalist is the actor
    "unimoral_056": "Military",             # "military officer given a mission" mislabeled as Law Enforcement
    "unimoral_064": "Government",           # "government official has 100 vaccines" mislabeled as Healthcare
}

# Check current values and only fix if actually wrong
applied = 0
for s in scenarios:
    sid = s["scenario_id"]
    if sid in FINAL_FIXES and s["domain"] != FINAL_FIXES[sid]:
        old = s["domain"]
        s["domain"] = FINAL_FIXES[sid]
        applied += 1
        print(f"FIXED: {sid}: {old} -> {FINAL_FIXES[sid]}")

# Also check unimoral_026, 049, 052 — are they already correct?
for sid in ["unimoral_026", "unimoral_049", "unimoral_052"]:
    for s in scenarios:
        if s["scenario_id"] == sid:
            print(f"KEPT: {sid}: {s['domain']} (actor is {s['decision_maker_role']})")

print(f"\nApplied {applied} domain fixes")

# Save
with open("data/curated/production_scenarios.json", "w", encoding="utf-8") as f:
    json.dump(scenarios, f, indent=2, ensure_ascii=False)
print("Saved production_scenarios.json")

# Also fix validation_scenarios.json
with open("data/curated/validation_scenarios.json", "r", encoding="utf-8") as f:
    val_scenarios = json.load(f)

val_fixed = 0
for s in val_scenarios:
    sid = s["scenario_id"]
    if sid in FINAL_FIXES and s["domain"] != FINAL_FIXES[sid]:
        old = s["domain"]
        s["domain"] = FINAL_FIXES[sid]
        val_fixed += 1
        print(f"FIXED (validation): {sid}: {old} -> {FINAL_FIXES[sid]}")

with open("data/curated/validation_scenarios.json", "w", encoding="utf-8") as f:
    json.dump(val_scenarios, f, indent=2, ensure_ascii=False)
print(f"Saved validation_scenarios.json ({val_fixed} fixes)")

# Final domain distribution
from collections import Counter
domain_counts = Counter(s["domain"] for s in scenarios)
print("\nFinal domain distribution:")
for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
    print(f"  {d}: {c}")
