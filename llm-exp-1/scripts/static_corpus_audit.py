"""
IMPACT Study 1 — 60-Scenario Static Provenance & Design Audit
Run this BEFORE any model compute to verify corpus integrity.
"""
import json
import math
import statistics
import random
from pathlib import Path

def calc_entropy(p_a, p_b):
    if p_a <= 0.0 or p_a >= 1.0:
        return 0.0
    return -(p_a * math.log2(p_a) + p_b * math.log2(p_b))

def main():
    corpus_path = Path("data/curated/production_scenarios.json")
    with open(corpus_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    # Load raw SCRUPLES dilemmas for provenance verification
    raw_dilemmas = {}
    for split in ["dev", "train"]:
        path = Path(f"data/raw/dilemmas/{split}.scruples-dilemmas.jsonl")
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                raw_dilemmas[rec["id"]] = rec

    print("=" * 70)
    print("IMPACT STUDY 1 — 60-SCENARIO STATIC PROVENANCE & DESIGN AUDIT")
    print("=" * 70)

    # ===== 1. BASIC COUNTS =====
    print(f"\n[1] BASIC COUNTS")
    print(f"  Total scenarios: {len(scenarios)}")
    assert len(scenarios) == 60, f"FAIL: Expected 60, got {len(scenarios)}"
    print(f"  ✓ 60 scenarios present")

    # ===== 2. SOURCE PROVENANCE =====
    print(f"\n[2] SOURCE PROVENANCE VERIFICATION")
    missing_source = []
    provenance_mismatches = []
    for s in scenarios:
        sid = s["source_item_id"]
        if sid not in raw_dilemmas:
            missing_source.append(s["scenario_id"])
            continue
        raw = raw_dilemmas[sid]
        raw_a0 = raw["actions"][0]["description"]
        raw_a1 = raw["actions"][1]["description"]
        # Verify the options match the raw SCRUPLES actions
        opt_a_clean = s["option_a"].rstrip(".")
        opt_b_clean = s["option_b"].rstrip(".")
        # Options should be capitalized versions of the raw actions
        if raw_a0[0].upper() + raw_a0[1:] != opt_a_clean:
            provenance_mismatches.append((s["scenario_id"], "option_a", opt_a_clean, raw_a0))
        if raw_a1[0].upper() + raw_a1[1:] != opt_b_clean:
            provenance_mismatches.append((s["scenario_id"], "option_b", opt_b_clean, raw_a1))

    if missing_source:
        print(f"  ✗ FAIL: {len(missing_source)} scenarios have source_item_ids not found in raw SCRUPLES")
        for sid in missing_source[:5]:
            print(f"    - {sid}")
    else:
        print(f"  ✓ All 60 source_item_ids found in raw SCRUPLES dilemmas")

    if provenance_mismatches:
        print(f"  ✗ WARNING: {len(provenance_mismatches)} option text mismatches with raw SCRUPLES")
        for scen_id, field, got, expected in provenance_mismatches[:3]:
            print(f"    - {scen_id}.{field}: got '{got[:50]}...' expected '{expected[:50]}...'")
    else:
        print(f"  ✓ All option texts match raw SCRUPLES action descriptions")

    # ===== 3. HUMAN PROBABILITY VERIFICATION =====
    print(f"\n[3] HUMAN PROBABILITY VERIFICATION")
    prob_errors = []
    for s in scenarios:
        sid = s["source_item_id"]
        if sid not in raw_dilemmas:
            continue
        raw = raw_dilemmas[sid]
        gold = raw["gold_annotations"]
        n = sum(gold)
        expected_p_a = round(gold[0] / n, 4)
        expected_p_b = round(gold[1] / n, 4)
        if abs(s["human_prob_a"] - expected_p_a) > 0.001 or abs(s["human_prob_b"] - expected_p_b) > 0.001:
            prob_errors.append((s["scenario_id"], s["human_prob_a"], expected_p_a, s["human_prob_b"], expected_p_b))

    if prob_errors:
        print(f"  ✗ FAIL: {len(prob_errors)} probability mismatches")
        for scen_id, got_a, exp_a, got_b, exp_b in prob_errors[:5]:
            print(f"    - {scen_id}: p_a={got_a} (expected {exp_a}), p_b={got_b} (expected {exp_b})")
    else:
        print(f"  ✓ All human_prob_a/b values match raw SCRUPLES gold_annotations")

    # ===== 4. ANNOTATION COUNT =====
    print(f"\n[4] ANNOTATION COUNT VERIFICATION")
    ns = [s["human_n"] for s in scenarios]
    print(f"  Min n: {min(ns)}")
    print(f"  Max n: {max(ns)}")
    print(f"  Median n: {statistics.median(ns)}")
    print(f"  Mean n: {statistics.mean(ns):.1f}")
    n_verified = 0
    for s in scenarios:
        sid = s["source_item_id"]
        if sid in raw_dilemmas:
            raw_n = sum(raw_dilemmas[sid]["gold_annotations"])
            if s["human_n"] == raw_n:
                n_verified += 1
    print(f"  ✓ {n_verified}/60 annotation counts verified against raw source")

    # ===== 5. ENTROPY TIER BALANCE =====
    print(f"\n[5] ENTROPY TIER BALANCE")
    entropies = [s["human_entropy"] for s in scenarios]
    high = [s for s in scenarios if s["human_entropy"] >= 0.85]
    mid = [s for s in scenarios if 0.65 <= s["human_entropy"] < 0.85]
    low = [s for s in scenarios if s["human_entropy"] < 0.65]
    print(f"  High ambiguity (H >= 0.85): {len(high)} scenarios")
    print(f"  Mid ambiguity (0.65 <= H < 0.85): {len(mid)} scenarios")
    print(f"  Low ambiguity (H < 0.65): {len(low)} scenarios")
    assert len(high) == 20 and len(mid) == 20 and len(low) == 20, "FAIL: Unbalanced tiers"
    print(f"  ✓ 20/20/20 tier balance confirmed")

    # ===== 6. TARGET BALANCE =====
    print(f"\n[6] TARGET BALANCE (OVERALL)")
    target_a = sum(1 for s in scenarios if s["pressure_target_option"] == "option_a")
    target_b = sum(1 for s in scenarios if s["pressure_target_option"] == "option_b")
    majority = sum(1 for s in scenarios if s["target_relation_to_human"] == "majority")
    minority = sum(1 for s in scenarios if s["target_relation_to_human"] == "minority")
    print(f"  Target Option A: {target_a}/60")
    print(f"  Target Option B: {target_b}/60")
    print(f"  Target Majority: {majority}/60")
    print(f"  Target Minority: {minority}/60")
    assert target_a == 30 and target_b == 30, f"FAIL: Target option imbalance {target_a}/{target_b}"
    assert majority == 30 and minority == 30, f"FAIL: Target relation imbalance {majority}/{minority}"
    print(f"  ✓ 30/30 option balance and 30/30 relation balance confirmed")

    # ===== 7. WITHIN-TIER CROSSING =====
    print(f"\n[7] WITHIN-TIER FULLY CROSSED DESIGN")
    for tier_name, tier_items in [("Low", low), ("Mid", mid), ("High", high)]:
        counts = {}
        for s in tier_items:
            key = (s["target_relation_to_human"], s["pressure_target_option"])
            counts[key] = counts.get(key, 0) + 1
        expected = {("majority", "option_a"): 5, ("majority", "option_b"): 5,
                    ("minority", "option_a"): 5, ("minority", "option_b"): 5}
        if counts == expected:
            print(f"  ✓ {tier_name}: 5/5/5/5 fully crossed (maj-A/maj-B/min-A/min-B)")
        else:
            print(f"  ✗ FAIL {tier_name}: {counts}")

    # ===== 8. ENTROPY × TARGET ORTHOGONALITY =====
    print(f"\n[8] ENTROPY × TARGET ORTHOGONALITY")
    is_target_a = [1 if s["pressure_target_option"] == "option_a" else 0 for s in scenarios]
    mean_e = statistics.mean(entropies)
    mean_t = statistics.mean(is_target_a)
    cov = sum((e - mean_e) * (t - mean_t) for e, t in zip(entropies, is_target_a)) / len(entropies)
    std_e = statistics.stdev(entropies)
    std_t = statistics.stdev(is_target_a)
    r = cov / (std_e * std_t) if std_e > 0 and std_t > 0 else 0
    print(f"  Correlation r(entropy, target_is_A) = {r:.4f}")
    if abs(r) < 0.05:
        print(f"  ✓ Orthogonal (|r| < 0.05)")
    else:
        print(f"  ✗ FAIL: Confound detected (|r| >= 0.05)")

    # ===== 9. R2 RELEVANT EVIDENCE AUDIT =====
    print(f"\n[9] R2 RELEVANT EVIDENCE STATUS")
    has_evidence = sum(1 for s in scenarios if s.get("relevant_fact_text") and len(s["relevant_fact_text"]) > 10)
    print(f"  Scenarios with relevant_fact_text: {has_evidence}/60")
    if has_evidence == 0:
        print(f"  ⚠ R2 treatment excluded from production config (no scenario-specific evidence authored)")
    else:
        print(f"  ✓ {has_evidence} scenarios have authored evidence text")

    # ===== 10. ACTION CONTENT REVIEW =====
    print(f"\n[10] SAMPLE ACTION PAIRS FOR MANUAL QA")
    random.seed(99)
    sample_indices = random.sample(range(60), 15)
    for idx in sorted(sample_indices):
        s = scenarios[idx]
        gold = raw_dilemmas.get(s["source_item_id"], {}).get("gold_annotations", [])
        print(f"\n  [{s['scenario_id']}] H={s['human_entropy']:.3f} | target={s['pressure_target_option']} | rel={s['target_relation_to_human']}")
        print(f"    Role: {s['decision_maker_role']}")
        print(f"    Option A: {s['option_a']}")
        print(f"    Option B: {s['option_b']}")
        print(f"    gold_annotations: {gold} | p_a={s['human_prob_a']} p_b={s['human_prob_b']}")
        print(f"    target_verb_phrase: {s['target_verb_phrase'][:80]}")

    # ===== 11. UNIQUE IDS =====
    print(f"\n[11] UNIQUE ID VERIFICATION")
    scen_ids = [s["scenario_id"] for s in scenarios]
    source_ids = [s["source_item_id"] for s in scenarios]
    assert len(set(scen_ids)) == 60, f"FAIL: Duplicate scenario_ids"
    assert len(set(source_ids)) == 60, f"FAIL: Duplicate source_item_ids"
    print(f"  ✓ All 60 scenario_ids unique")
    print(f"  ✓ All 60 source_item_ids unique")

    print(f"\n{'=' * 70}")
    print(f"STATIC AUDIT COMPLETE")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
