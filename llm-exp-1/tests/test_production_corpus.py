import pytest
from pathlib import Path
from impact.datasets.scruples import ScruplesAdapter
from impact.schemas import Scenario, Treatment, ProtocolVersion
from impact.scenarios.treatments import get_pilot_treatments
from impact.scenarios.renderer import render_prompt

def test_production_adapter_loading():
    adapter = ScruplesAdapter(data_dir=Path("data"), mode="production")
    scenarios = adapter.load_or_fetch()
    assert len(scenarios) == 64
    
    # Target option balance check
    target_a = sum(1 for s in scenarios if s.pressure_target_option == "option_a")
    target_b = sum(1 for s in scenarios if s.pressure_target_option == "option_b")
    assert target_a == 32
    assert target_b == 32
    
    # Target relation balance check
    rel_maj = sum(1 for s in scenarios if s.target_relation_to_human == "majority")
    rel_min = sum(1 for s in scenarios if s.target_relation_to_human == "minority")
    assert rel_maj == 32
    assert rel_min == 32
    
    # Provenance audit
    for s in scenarios:
        assert s.source_item_id is not None and len(s.source_item_id) > 0
        assert s.source_dataset == "UniMoral_v1.0_english"
        assert s.original_text is not None and len(s.original_text) > 0
        assert s.human_n is not None and s.human_n >= 3
        assert 0.0 <= s.human_entropy <= 1.0
    
    # Entropy x target orthogonality check
    import statistics
    entropies = [s.human_entropy for s in scenarios]
    is_target_a = [1 if s.pressure_target_option == "option_a" else 0 for s in scenarios]
    mean_e = statistics.mean(entropies)
    mean_t = statistics.mean(is_target_a)
    cov = sum((e - mean_e) * (t - mean_t) for e, t in zip(entropies, is_target_a)) / len(entropies)
    std_e = statistics.stdev(entropies)
    std_t = statistics.stdev(is_target_a)
    r = cov / (std_e * std_t) if std_e > 0 and std_t > 0 else 0
    assert abs(r) < 0.05, f"Entropy x target_option_a correlation too high: r={r:.4f}"

def test_production_adapter_hard_fail(tmp_path):
    # Non-existent directory in production mode should raise FileNotFoundError
    adapter = ScruplesAdapter(data_dir=tmp_path / "empty_dir", mode="production")
    with pytest.raises(FileNotFoundError) as exc_info:
        adapter.load_or_fetch()
    assert "PRODUCTION MODE ERROR" in str(exc_info.value)

def test_bidirectional_rendering():
    adapter = ScruplesAdapter(data_dir=Path("data"), mode="production")
    scenarios = adapter.load_or_fetch()
    treatments = get_pilot_treatments()
    authority_treatment = next(t for t in treatments if t.treatment_id == "P1_authority_pressure")
    
    # Test rendering for both option_a target and option_b target
    scen_target_a = next(s for s in scenarios if s.pressure_target_option == "option_a")
    scen_target_b = next(s for s in scenarios if s.pressure_target_option == "option_b")
    
    rendered_a = render_prompt(scen_target_a, authority_treatment, ProtocolVersion.VERSION_J, choice_order_reversed=False)
    rendered_b = render_prompt(scen_target_b, authority_treatment, ProtocolVersion.VERSION_J, choice_order_reversed=False)
    
    assert "INSTITUTIONAL CONTEXT:" in rendered_a.full_prompt_text
    assert "INSTITUTIONAL CONTEXT:" in rendered_b.full_prompt_text
    assert scen_target_a.target_verb_phrase.lower() in rendered_a.full_prompt_text.lower()
    assert scen_target_b.target_verb_phrase.lower() in rendered_b.full_prompt_text.lower()
