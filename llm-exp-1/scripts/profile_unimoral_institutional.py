"""
Deep profile of UniMoral English scenarios for IMPACT institutional eligibility.
Focuses on: scenario content, action text, source type, and institutional plausibility.
"""
import json
import math
import ast
from pathlib import Path
from collections import Counter

with open("data/raw/unimoral/english_scenario_profiles.json", "r", encoding="utf-8") as f:
    scenarios = json.load(f)

print(f"Total scenarios: {len(scenarios)}")

# Source distribution
reddit = [s for s in scenarios if s["scenario_id"].startswith("Reddit_")]
psych_long = [s for s in scenarios if s["scenario_id"].startswith("long_")]
psych_short = [s for s in scenarios if s["scenario_id"].startswith("short_")]
print(f"\nBy source:")
print(f"  Reddit-derived: {len(reddit)}")
print(f"  Psychological (long): {len(psych_long)}")
print(f"  Psychological (short): {len(psych_short)}")

# Entropy distribution (only 2 possible values with n=3)
entropy_counts = Counter(s["entropy"] for s in scenarios)
print(f"\nEntropy distribution (n=3 per item):")
for e, count in sorted(entropy_counts.items()):
    label = "unanimous (3-0)" if e == 0.0 else "split (2-1)"
    print(f"  H={e:.4f} ({label}): {count} scenarios")

# For IMPACT we need 3 tiers. With n=3 we only get 2 entropy values.
# But the *psychological* scenarios (MJI, DIT, MCT) were designed to test
# moral judgment stages — they might have inherently different difficulty.
# Let's check if we can use the theory_factor as a proxy.
print("\n=== SCENARIO ID STRUCTURE ===")
# Parse scenario IDs to understand contributing factors
factors = Counter()
theories = Counter()
for s in scenarios:
    sid = s["scenario_id"]
    parts = sid.split("_")
    if sid.startswith("Reddit_"):
        factors["Reddit"] += 1
    else:
        # e.g., "long_id_0_MJI_Emotions" or "short_id_142_MCT_Sacred Values"
        if len(parts) >= 4:
            theory = parts[3]
            theories[theory] += 1
            if len(parts) >= 5:
                factor = "_".join(parts[4:])
                factors[factor] += 1

print("Theories:", dict(theories))
print("Factors:", dict(factors))

# Institutional keyword screening
INSTITUTIONAL_KEYWORDS = [
    "manager", "employee", "boss", "supervisor", "company", "corporate",
    "teacher", "student", "professor", "school", "university", "class", "grade",
    "doctor", "patient", "nurse", "hospital", "medical", "clinic",
    "lawyer", "client", "court", "judge",
    "researcher", "participant", "study", "experiment",
    "journalist", "editor", "news", "report",
    "officer", "police", "government", "policy",
    "landlord", "tenant", "rent",
    "engineer", "safety", "product",
    "volunteer", "charity", "nonprofit",
    "colleague", "coworker", "team", "department",
    "promotion", "hire", "fire", "workplace",
    "confidential", "whistleblow", "compliance",
    "budget", "resource", "allocation",
    "HR", "human resources",
]

def check_institutional(text):
    """Check if scenario text contains institutional keywords."""
    lower = text.lower()
    matches = [kw for kw in INSTITUTIONAL_KEYWORDS if kw in lower]
    return matches

institutional_candidates = []
for s in scenarios:
    text = s["scenario_text"] + " " + s["possible_actions_raw"]
    matches = check_institutional(text)
    if matches:
        s["institutional_keywords"] = matches
        institutional_candidates.append(s)

print(f"\n=== INSTITUTIONAL ELIGIBILITY ===")
print(f"Scenarios with institutional keywords: {len(institutional_candidates)} / {len(scenarios)}")

# Split by entropy
inst_high_h = [s for s in institutional_candidates if s["entropy"] >= 0.85]
inst_low_h = [s for s in institutional_candidates if s["entropy"] < 0.65]
print(f"  High entropy (split 2-1): {len(inst_high_h)}")
print(f"  Low entropy (unanimous 3-0): {len(inst_low_h)}")

# Print all institutional candidates with their scenario text
print(f"\n=== ALL INSTITUTIONAL CANDIDATES (first 40) ===")
for i, s in enumerate(institutional_candidates[:40]):
    entropy_label = "SPLIT(2-1)" if s["entropy"] >= 0.85 else "UNANIMOUS(3-0)"
    print(f"\n  [{i+1}] {s['scenario_id']} | {entropy_label} | n={s['n']}")
    print(f"    Keywords: {s['institutional_keywords']}")
    print(f"    Scenario: {s['scenario_text'][:250]}")
    # Parse actions
    try:
        actions = ast.literal_eval(s["possible_actions_raw"])
        if isinstance(actions, list):
            for j, a in enumerate(actions):
                print(f"    Action {j+1}: {str(a)[:150]}")
    except:
        print(f"    Actions raw: {s['possible_actions_raw'][:200]}")
    print(f"    Votes: {s['action_counts']}")

# Summary stats
print(f"\n=== SUMMARY FOR IMPACT FEASIBILITY ===")
print(f"Total English scenarios: {len(scenarios)}")
print(f"With institutional keywords: {len(institutional_candidates)}")
print(f"  - Split (2-1, H=0.918): {len(inst_high_h)}")
print(f"  - Unanimous (3-0, H=0.0): {len(inst_low_h)}")
print(f"\nFor 60-scenario IMPACT design (3 tiers x 20):")
print(f"  With n=3, we only have 2 distinct entropy values.")
print(f"  Options:")
print(f"    A) Use 2 tiers instead of 3 (30 split + 30 unanimous)")
print(f"    B) Use a different tier variable (scenario source, contributing factor)")
print(f"    C) Accept 2 tiers as adequate for Study 1")
