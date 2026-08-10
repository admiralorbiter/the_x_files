"""Audit all 64 production scenario domain labels and fix mismatches."""
import json
from pathlib import Path

with open("data/curated/production_scenarios.json", "r", encoding="utf-8") as f:
    scenarios = json.load(f)

print(f"Total scenarios: {len(scenarios)}\n")
print(f"{'ID':15s} | {'Role':22s} | {'Domain':25s} | Scenario (first 140 chars)")
print("-" * 210)

# Flag potential mismatches based on keyword analysis
DOMAIN_KEYWORDS = {
    "Healthcare": ["doctor", "patient", "hospital", "medical", "nurse", "surgeon", "transplant", "triage", "clinical", "treatment"],
    "Corporate/Workplace": ["manager", "employee", "company", "corporate", "workplace", "promotion", "boss", "team", "hire", "fire", "underperform"],
    "Education": ["teacher", "student", "school", "university", "professor", "class", "grade", "academic"],
    "Legal": ["lawyer", "court", "judge", "legal", "attorney", "client", "defense"],
    "Media/Journalism": ["journalist", "reporter", "editor", "news", "media", "publish", "story"],
    "Law Enforcement": ["police", "officer", "crime", "suspect", "detective", "arrest"],
    "Research": ["researcher", "scientist", "experiment", "study", "findings", "discovery"],
    "Military": ["military", "soldier", "commander", "war", "troops", "combat", "battlefield"],
    "Government": ["government", "official", "policy", "public", "legislation"],
    "Social Services": ["social worker", "counselor", "community", "welfare"],
}

fixes = {}
for s in scenarios:
    kernel_lower = (s["ethical_kernel"] + " " + s["option_a"] + " " + s["option_b"]).lower()
    current_domain = s["domain"]
    
    # Score each domain
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in kernel_lower)
        if score > 0:
            scores[domain] = score
    
    # Find best match
    best_domain = max(scores, key=scores.get) if scores else current_domain
    
    mismatch = ""
    if best_domain != current_domain and scores.get(best_domain, 0) > scores.get(current_domain, 0):
        mismatch = f" ** SUGGEST: {best_domain} (score {scores[best_domain]} vs {scores.get(current_domain, 0)})"
        fixes[s["scenario_id"]] = best_domain
    
    print(f"{s['scenario_id']:15s} | {s['decision_maker_role']:22s} | {current_domain:25s} | {s['ethical_kernel'][:140]}{mismatch}")

print(f"\n\nSuggested fixes: {len(fixes)}")
for sid, new_domain in fixes.items():
    print(f"  {sid}: -> {new_domain}")
