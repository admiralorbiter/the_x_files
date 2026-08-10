"""
Render all 9 treatment conditions for 3 sample UniMoral scenarios.
Manual QA of semantic framing with genuine institutional dilemmas.
"""
import json
from pathlib import Path
from impact.datasets.scruples import ScruplesAdapter
from impact.scenarios.treatments import get_pilot_treatments
from impact.scenarios.renderer import render_prompt
from impact.schemas import ProtocolVersion

def main():
    adapter = ScruplesAdapter(data_dir=Path("data"), mode="production")
    scenarios = adapter.load_or_fetch()
    treatments = get_pilot_treatments()
    
    # Exclude R2
    treatments = [t for t in treatments if t.treatment_id != "R2_relevant_evidence"]
    
    # Pick 3 scenarios: 1 unanimous, 1 divided, different domains
    samples = []
    # First unanimous
    for s in scenarios:
        if s.human_entropy == 0.0 and s.decision_maker_role not in [x.decision_maker_role for x in samples]:
            samples.append(s)
            break
    # First divided
    for s in scenarios:
        if s.human_entropy > 0.0 and s.decision_maker_role not in [x.decision_maker_role for x in samples]:
            samples.append(s)
            break
    # Third with different domain
    for s in scenarios:
        if s.decision_maker_role not in [x.decision_maker_role for x in samples]:
            samples.append(s)
            break
    
    for scen in samples:
        agreement = "UNANIMOUS (3/3)" if scen.human_entropy == 0.0 else "DIVIDED (2/1)"
        print("=" * 80)
        print(f"SCENARIO: {scen.scenario_id} | {agreement}")
        print(f"Role: {scen.decision_maker_role} | Domain: {scen.domain}")
        print(f"Target: {scen.pressure_target_option} | Relation: {scen.target_relation_to_human}")
        print(f"human_prob_a: {scen.human_prob_a} | human_prob_b: {scen.human_prob_b}")
        print(f"\nOption A: {scen.option_a[:150]}")
        print(f"Option B: {scen.option_b[:150]}")
        print("=" * 80)
        
        # Only show B0, P1, and C1 for brevity
        key_treatments = [t for t in treatments if t.treatment_id in [
            "B0_stripped_baseline",
            "C1_authority_neutral",
            "P1_authority_pressure",
            "P2_incentive_pressure",
            "P3_social_pressure",
        ]]
        
        for treatment in key_treatments:
            rendered = render_prompt(
                scenario=scen,
                treatment=treatment,
                protocol_version=ProtocolVersion.VERSION_J,
                choice_order_reversed=False,
            )
            print(f"\n--- {treatment.treatment_id} ---")
            print(rendered.full_prompt_text)
            print()

if __name__ == "__main__":
    main()
