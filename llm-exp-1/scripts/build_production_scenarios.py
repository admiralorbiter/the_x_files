"""
IMPACT Study 1 — UniMoral Corpus Curation Pipeline

Design: 2 agreement strata × 2 target relations × 2 target sides × 8 = 64 scenarios
Production: 64 × 9 treatments × 2 models × 2 option orders = 2,304 cells

Agreement strata (NOT "ambiguity tiers"):
  - Unanimous: all 3 annotators selected the same action (H=0.000)
  - Divided: 2 annotators selected one action, 1 selected the other (H=0.918)

Target relation:
  - majority: pressure pushes toward the action chosen by more annotators
  - minority: pressure pushes toward the action chosen by fewer annotators

Target side:
  - option_a: the pressure target is placed in the Option A position
  - option_b: the pressure target is placed in the Option B position
"""

import json
import math
import ast
import random
from pathlib import Path
from collections import defaultdict

def calc_entropy(p_a, p_b):
    if p_a <= 0.0 or p_a >= 1.0:
        return 0.0
    return -(p_a * math.log2(p_a) + p_b * math.log2(p_b))

# ── Load scenario profiles ──────────────────────────────────────────────
with open("data/raw/unimoral/english_scenario_profiles.json", "r", encoding="utf-8") as f:
    all_scenarios = json.load(f)

# ── Load full scenario text from CSVs for richer data ────────────────────
import pandas as pd

HF_CACHE = Path.home() / ".cache/huggingface/hub/datasets--shivaniku--UniMoral/snapshots/d74cd5140261a58456727606f10ea31de06365e8"
dfs = []
for fname in ["English_long_formatted.csv", "English_short_formatted.csv"]:
    dfs.append(pd.read_csv(HF_CACHE / fname))
df_all = pd.concat(dfs, ignore_index=True)

# Build full scenario lookup: one record per scenario with all annotator choices
scenario_data = {}
for sid, group in df_all.groupby("Scenario_id"):
    rows = group.to_dict("records")
    scenario_text = rows[0]["Scenario"]
    possible_raw = rows[0]["Possible_actions"]
    try:
        possible_actions = ast.literal_eval(possible_raw)
    except:
        continue
    if not isinstance(possible_actions, list) or len(possible_actions) != 2:
        continue
    
    selected = [int(r["Selected_action"]) for r in rows]
    count_1 = selected.count(1)
    count_2 = selected.count(2)
    n = len(selected)
    
    # Determine majority/minority
    if count_1 > count_2:
        majority_idx = 0  # action 1 (0-indexed)
        minority_idx = 1
        majority_count = count_1
        minority_count = count_2
    elif count_2 > count_1:
        majority_idx = 1  # action 2 (0-indexed)
        minority_idx = 0
        majority_count = count_2
        minority_count = count_1
    else:
        # Tie — skip (shouldn't happen with n=3)
        continue
    
    p_maj = majority_count / n
    p_min = minority_count / n
    entropy = calc_entropy(p_maj, p_min)
    
    # Agreement stratum
    if minority_count == 0:
        agreement = "unanimous"
    else:
        agreement = "divided"
    
    # Get contributing factors etc from long-form data
    action_criteria = rows[0].get("Action_criteria", None)
    contributing_factors = rows[0].get("Contributing_factors", None)
    
    # Source type
    if sid.startswith("Reddit_"):
        source_type = "reddit"
    else:
        source_type = "psychological"
    
    scenario_data[sid] = {
        "scenario_id": sid,
        "scenario_text": scenario_text,
        "action_1": possible_actions[0],
        "action_2": possible_actions[1],
        "majority_idx": majority_idx,
        "minority_idx": minority_idx,
        "majority_count": majority_count,
        "minority_count": minority_count,
        "n": n,
        "entropy": round(entropy, 6),
        "agreement": agreement,
        "source_type": source_type,
        "action_criteria": str(action_criteria) if action_criteria else None,
        "contributing_factors": str(contributing_factors) if contributing_factors else None,
    }

print(f"Total scenarios with clean binary actions: {len(scenario_data)}")

# ── Institutional plausibility screening ─────────────────────────────────

# The reviewer's 5-question test:
# 1. Does the actor have a plausible supervisor or authority?
# 2. Could their performance evaluation plausibly relate to this choice?
# 3. Could professional peers plausibly express a norm?
# 4. Could an organizational metric plausibly favor an outcome?
# 5. Does adding those contexts feel natural rather than absurd?

# Automated keyword scoring as first-pass filter
STRONG_INSTITUTIONAL = [
    "manager", "employee", "boss", "supervisor", "company", "corporate", "workplace",
    "promotion", "hire", "fire", "coworker", "colleague",
    "teacher", "professor", "school", "university", "principal",
    "doctor", "patient", "nurse", "hospital", "medical", "clinic", "surgeon",
    "lawyer", "client", "court", "judge", "attorney",
    "officer", "police", "government", "official",
    "researcher", "participant", "experiment",
    "journalist", "editor", "reporter",
    "engineer", "safety standard",
    "social worker", "counselor",
    "landlord", "tenant",
    "military", "soldier", "commander",
    "ceo", "executive", "board",
]

MODERATE_INSTITUTIONAL = [
    "report", "policy", "budget", "resource", "allocation",
    "team", "department", "organization", "institution",
    "confidential", "whistleblow", "compliance", "ethics committee",
    "volunteer", "charity", "nonprofit",
    "community", "public service",
    "student",  # weaker — could be peer not institutional
]

def score_institutional(s):
    """Score institutional plausibility (higher = more plausible)."""
    text = (s["scenario_text"] + " " + s["action_1"] + " " + s["action_2"]).lower()
    
    strong_hits = sum(1 for kw in STRONG_INSTITUTIONAL if kw in text)
    moderate_hits = sum(1 for kw in MODERATE_INSTITUTIONAL if kw in text)
    
    score = strong_hits * 3 + moderate_hits * 1
    keywords = [kw for kw in STRONG_INSTITUTIONAL + MODERATE_INSTITUTIONAL if kw in text]
    
    return score, keywords

candidates = []
for sid, s in scenario_data.items():
    score, keywords = score_institutional(s)
    if score >= 3:  # At least one strong keyword hit
        s["inst_score"] = score
        s["inst_keywords"] = keywords
        candidates.append(s)

print(f"Candidates with institutional score >= 3: {len(candidates)}")

# Split by agreement stratum
unanimous = [c for c in candidates if c["agreement"] == "unanimous"]
divided = [c for c in candidates if c["agreement"] == "divided"]
print(f"  Unanimous (3/3): {len(unanimous)}")
print(f"  Divided (2/1): {len(divided)}")

# ── Sort by institutional score (higher = more natural fit) ──────────────
unanimous.sort(key=lambda x: -x["inst_score"])
divided.sort(key=lambda x: -x["inst_score"])

# ── Select 32 per stratum with target crossing ──────────────────────────
# Within each stratum, we need:
#   majority-target + option_a: 8 scenarios
#   majority-target + option_b: 8 scenarios
#   minority-target + option_a: 8 scenarios
#   minority-target + option_b: 8 scenarios

random.seed(42)

def select_with_crossing(pool, n_per_cell=8):
    """Select scenarios and assign target relation + target side."""
    # Shuffle to randomize within score tiers
    random.shuffle(pool)
    # Re-sort by score to prefer higher institutional plausibility
    pool.sort(key=lambda x: -x["inst_score"])
    
    selected = []
    needed = n_per_cell * 4  # 4 cells per stratum
    
    if len(pool) < needed:
        print(f"  WARNING: Only {len(pool)} candidates available, need {needed}")
        needed = len(pool)
    
    items = pool[:needed]
    
    # Assign cells in round-robin
    cells = [
        ("majority", "option_a"),
        ("majority", "option_b"),
        ("minority", "option_a"),
        ("minority", "option_b"),
    ]
    
    for i, item in enumerate(items):
        target_relation, target_side = cells[i % 4]
        
        # Determine which action goes in which option position
        # majority_idx and minority_idx are 0-indexed into [action_1, action_2]
        if target_relation == "majority":
            target_action_idx = item["majority_idx"]
        else:
            target_action_idx = item["minority_idx"]
        
        # target_side determines where the target goes
        if target_side == "option_a":
            # Target action goes to Option A position
            if target_action_idx == 0:
                opt_a = item["action_1"]
                opt_b = item["action_2"]
                # human_prob_a = majority proportion if target is majority, minority if target is minority
                if target_relation == "majority":
                    h_p_a = item["majority_count"] / item["n"]
                    h_p_b = item["minority_count"] / item["n"]
                else:
                    h_p_a = item["minority_count"] / item["n"]
                    h_p_b = item["majority_count"] / item["n"]
            else:
                # action_2 is target, swap to Option A
                opt_a = item["action_2"]
                opt_b = item["action_1"]
                if target_relation == "majority":
                    h_p_a = item["majority_count"] / item["n"]
                    h_p_b = item["minority_count"] / item["n"]
                else:
                    h_p_a = item["minority_count"] / item["n"]
                    h_p_b = item["majority_count"] / item["n"]
        else:
            # Target action goes to Option B position
            if target_action_idx == 0:
                # action_1 is target, goes to Option B
                opt_a = item["action_2"]
                opt_b = item["action_1"]
                if target_relation == "majority":
                    h_p_a = item["minority_count"] / item["n"]
                    h_p_b = item["majority_count"] / item["n"]
                else:
                    h_p_a = item["majority_count"] / item["n"]
                    h_p_b = item["minority_count"] / item["n"]
            else:
                # action_2 is target, stays in Option B
                opt_a = item["action_1"]
                opt_b = item["action_2"]
                if target_relation == "majority":
                    h_p_a = item["minority_count"] / item["n"]
                    h_p_b = item["majority_count"] / item["n"]
                else:
                    h_p_a = item["majority_count"] / item["n"]
                    h_p_b = item["minority_count"] / item["n"]
        
        # Infer decision-maker role from scenario text
        role = infer_role(item["scenario_text"])
        
        # Build the target verb phrase from the target action
        if target_side == "option_a":
            target_action_text = opt_a
        else:
            target_action_text = opt_b
        
        # Clean up action text for verb phrase (lowercase, remove trailing period)
        tvp = target_action_text.strip().rstrip(".")
        if tvp[0].isupper():
            tvp = tvp[0].lower() + tvp[1:]
        
        selected.append({
            "source_scenario_id": item["scenario_id"],
            "scenario_text": item["scenario_text"],
            "original_action_1": item["action_1"],
            "original_action_2": item["action_2"],
            "option_a": opt_a,
            "option_b": opt_b,
            "pressure_target_option": target_side,
            "target_relation_to_human": target_relation,
            "target_verb_phrase": tvp,
            "human_prob_a": round(h_p_a, 4),
            "human_prob_b": round(h_p_b, 4),
            "human_entropy": item["entropy"],
            "human_n": item["n"],
            "human_majority_count": item["majority_count"],
            "human_minority_count": item["minority_count"],
            "agreement_stratum": item["agreement"],
            "decision_maker_role": role,
            "domain": infer_domain(item["scenario_text"]),
            "source_type": item["source_type"],
            "inst_score": item["inst_score"],
            "inst_keywords": item["inst_keywords"],
        })
    
    return selected

def infer_role(text):
    """Infer a natural decision-maker role from scenario text."""
    lower = text.lower()
    if any(w in lower for w in ["manager", "executive", "ceo", "boss", "supervisor"]):
        return "Manager"
    if any(w in lower for w in ["doctor", "surgeon", "physician", "clinician"]):
        return "Doctor"
    if any(w in lower for w in ["teacher", "professor", "instructor", "principal"]):
        return "Teacher"
    if any(w in lower for w in ["lawyer", "attorney", "advocate"]):
        return "Lawyer"
    if any(w in lower for w in ["journalist", "reporter", "editor"]):
        return "Journalist"
    if any(w in lower for w in ["officer", "police", "detective"]):
        return "Police Officer"
    if any(w in lower for w in ["researcher", "scientist"]):
        return "Researcher"
    if any(w in lower for w in ["engineer"]):
        return "Engineer"
    if any(w in lower for w in ["nurse"]):
        return "Nurse"
    if any(w in lower for w in ["social worker", "counselor"]):
        return "Social Worker"
    if any(w in lower for w in ["soldier", "military", "commander"]):
        return "Military Officer"
    if any(w in lower for w in ["landlord"]):
        return "Landlord"
    if any(w in lower for w in ["employee", "worker", "staff"]):
        return "Employee"
    if any(w in lower for w in ["government", "official", "administrator"]):
        return "Government Official"
    return "Professional"

def infer_domain(text):
    lower = text.lower()
    if any(w in lower for w in ["doctor", "patient", "hospital", "medical", "nurse", "surgeon", "transplant"]):
        return "Healthcare"
    if any(w in lower for w in ["teacher", "student", "school", "university", "professor", "class"]):
        return "Education"
    if any(w in lower for w in ["lawyer", "court", "judge", "legal", "attorney"]):
        return "Legal"
    if any(w in lower for w in ["journalist", "reporter", "editor", "news", "media"]):
        return "Media/Journalism"
    if any(w in lower for w in ["police", "officer", "crime", "suspect"]):
        return "Law Enforcement"
    if any(w in lower for w in ["researcher", "scientist", "experiment", "study"]):
        return "Research"
    if any(w in lower for w in ["military", "soldier", "commander", "war"]):
        return "Military"
    if any(w in lower for w in ["manager", "employee", "company", "corporate", "workplace", "promotion", "boss"]):
        return "Corporate/Workplace"
    if any(w in lower for w in ["social worker", "counselor", "community"]):
        return "Social Services"
    if any(w in lower for w in ["government", "official", "policy", "public"]):
        return "Government"
    if any(w in lower for w in ["landlord", "tenant"]):
        return "Housing"
    return "General Professional"

# ── Select 32 per stratum ────────────────────────────────────────────────
print("\n=== SELECTING UNANIMOUS STRATUM (32 scenarios) ===")
sel_unanimous = select_with_crossing(unanimous, n_per_cell=8)
print(f"  Selected: {len(sel_unanimous)}")

print("\n=== SELECTING DIVIDED STRATUM (32 scenarios) ===")
sel_divided = select_with_crossing(divided, n_per_cell=8)
print(f"  Selected: {len(sel_divided)}")

# ── Combine and assign final IDs ─────────────────────────────────────────
all_selected = sel_unanimous + sel_divided
for i, s in enumerate(all_selected):
    s["scenario_id"] = f"unimoral_{i+1:03d}"

print(f"\n=== TOTAL SELECTED: {len(all_selected)} ===")

# ── Build production_scenarios.json ──────────────────────────────────────
production = []
for s in all_selected:
    production.append({
        "scenario_id": s["scenario_id"],
        "ethical_kernel": s["scenario_text"],
        "decision_maker_role": s["decision_maker_role"],
        "option_a": s["option_a"],
        "option_b": s["option_b"],
        "option_a_id": None,
        "option_b_id": None,
        "pressure_target_option": s["pressure_target_option"],
        "target_verb_phrase": s["target_verb_phrase"],
        "target_relation_to_human": s["target_relation_to_human"],
        "relevant_fact_text": None,
        "human_prob_a": s["human_prob_a"],
        "human_prob_b": s["human_prob_b"],
        "human_entropy": s["human_entropy"],
        "domain": s["domain"],
        "source_dataset": "UniMoral_v1.0_english",
        "source_item_id": s["source_scenario_id"],
        "original_text": json.dumps({
            "original_action_1": s["original_action_1"],
            "original_action_2": s["original_action_2"],
        }),
        "human_n": s["human_n"],
        "scruples_split": None,
        "adaptation_notes": f"Direct UniMoral scenario. Agreement: {s['agreement_stratum']} ({s['human_majority_count']}-{s['human_minority_count']}). "
                           f"Actions used verbatim from UniMoral Possible_actions. "
                           f"Scenario text standardized by LLM (UniMoral methodology), human annotations are genuine Prolific annotator choices.",
        "adaptation_version": "v4.0_unimoral",
    })

out_path = Path("data/curated/production_scenarios.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(production, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(production)} production scenarios to {out_path}")

# ── Save detailed candidate list for manual review ───────────────────────
review_path = Path("data/curated/unimoral_candidates_for_review.json")
with open(review_path, "w", encoding="utf-8") as f:
    json.dump(all_selected, f, indent=2, ensure_ascii=False)
print(f"Saved detailed candidate list to {review_path}")

# ── Design audit ─────────────────────────────────────────────────────────
import statistics

print("\n" + "=" * 70)
print("CORPUS DESIGN AUDIT")
print("=" * 70)

print(f"\nTotal scenarios: {len(production)}")

# Agreement stratum balance
unan = sum(1 for s in production if s["human_entropy"] == 0.0)
div = sum(1 for s in production if s["human_entropy"] > 0.0)
print(f"\nAgreement strata:")
print(f"  Unanimous (3/3): {unan}")
print(f"  Divided (2/1): {div}")

# Target balance
ta = sum(1 for s in production if s["pressure_target_option"] == "option_a")
tb = sum(1 for s in production if s["pressure_target_option"] == "option_b")
print(f"\nTarget side:")
print(f"  option_a: {ta}")
print(f"  option_b: {tb}")

# Target relation balance
maj = sum(1 for s in production if s["target_relation_to_human"] == "majority")
mino = sum(1 for s in production if s["target_relation_to_human"] == "minority")
print(f"\nTarget relation:")
print(f"  majority: {maj}")
print(f"  minority: {mino}")

# Within-stratum crossing
print(f"\nWithin-stratum crossing:")
for stratum_label, h_val in [("Unanimous", 0.0), ("Divided", 0.918)]:
    stratum = [s for s in production if (s["human_entropy"] == 0.0) == (h_val == 0.0)]
    counts = {}
    for s in stratum:
        key = (s["target_relation_to_human"], s["pressure_target_option"])
        counts[key] = counts.get(key, 0) + 1
    print(f"  {stratum_label}: {counts}")

# Domain diversity
domains = [s["domain"] for s in production]
domain_counts = defaultdict(int)
for d in domains:
    domain_counts[d] += 1
print(f"\nDomain distribution:")
for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
    print(f"  {d}: {c}")

# Role diversity
roles = [s["decision_maker_role"] for s in production]
role_counts = defaultdict(int)
for r in roles:
    role_counts[r] += 1
print(f"\nRole distribution:")
for r, c in sorted(role_counts.items(), key=lambda x: -x[1]):
    print(f"  {r}: {c}")

# Source type
sources = [all_selected[i]["source_type"] for i in range(len(all_selected))]
src_counts = defaultdict(int)
for s in sources:
    src_counts[s] += 1
print(f"\nSource type:")
for s, c in sorted(src_counts.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

# Orthogonality check
entropies = [s["human_entropy"] for s in production]
is_target_a = [1 if s["pressure_target_option"] == "option_a" else 0 for s in production]
mean_e = statistics.mean(entropies)
mean_t = statistics.mean(is_target_a)
cov = sum((e - mean_e) * (t - mean_t) for e, t in zip(entropies, is_target_a)) / len(entropies)
std_e = statistics.stdev(entropies)
std_t = statistics.stdev(is_target_a)
r = cov / (std_e * std_t) if std_e > 0 and std_t > 0 else 0
print(f"\nOrthogonality: r(entropy, target_is_A) = {r:.4f}")

print(f"\nProduction design:")
print(f"  {len(production)} scenarios x 9 treatments x 2 models x 2 orders = {len(production)*9*2*2} cells")
