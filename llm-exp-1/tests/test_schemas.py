import pytest
from impact.schemas import (
    Scenario,
    Treatment,
    PressureFamily,
    NormativeRelevance,
    Direction,
    Intensity,
    GenerationConfig,
    ProtocolVersion,
)
from impact.utils.hashing import compute_cell_id


def test_scenario_entropy_validation():
    scenario = Scenario(
        scenario_id="s1",
        ethical_kernel="Kernel text",
        decision_maker_role="Role",
        option_a="Option A",
        option_b="Option B",
        human_prob_a=0.7,
        human_prob_b=0.3,
        human_entropy=0.881,
        domain="Workplace",
        source_dataset="SCRUPLES",
    )
    assert scenario.human_prob_a == 0.7
    assert scenario.human_entropy == 0.881


def test_deterministic_cell_id():
    gen_config = GenerationConfig(model_name="qwen3:14b", temperature=0.5)
    id1 = compute_cell_id(
        scenario_id="s1",
        treatment_id="t1",
        model_id="qwen3:14b",
        protocol_id=ProtocolVersion.VERSION_J,
        paraphrase_id="p0_default",
        replicate_index=0,
        generation_config=gen_config,
    )
    id2 = compute_cell_id(
        scenario_id="s1",
        treatment_id="t1",
        model_id="qwen3:14b",
        protocol_id=ProtocolVersion.VERSION_J,
        paraphrase_id="p0_default",
        replicate_index=0,
        generation_config=gen_config,
    )
    assert id1 == id2
    assert len(id1) == 64  # SHA-256 hex string length
