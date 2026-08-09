import os
import pytest
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.governor import Governor
from emergence_lab.scenarios.society_micro import build_micro_society_scenario
from emergence_lab.scenarios.socratic_academy import build_socratic_academy_scenario
from emergence_lab.domain.events import AgentAction, AgentTurnProposal
from emergence_lab.domain.telemetry import InferenceResult
from emergence_lab.engine.state_compiler import StateCompiler
from emergence_lab.engine.verifier import DeterministicVerifier
from emergence_lab.domain.dialogue_schemas import DialogueTurn
from emergence_lab.benchmarks.frozen_worlds import FROZEN_BENCHMARK_WORLDS, build_frozen_world_state

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_emergence.db")
    return EventRepository(db_path=db_file)

def test_target_agent_list_coercion():
    action = AgentAction(
        action_type="speak",
        target_agent=["Plato the Systematizer", "Heraclitus the Paradoxer"],
        message="What is virtue?",
        rationale="Dialogue with both"
    )
    assert action.target_agent == "Plato the Systematizer, Heraclitus the Paradoxer"

def test_socratic_scenario_build():
    state = build_socratic_academy_scenario("test_socratic_run")
    assert len(state.agents) == 3
    assert len(state.locations) == 3
    assert "Socrates the Gadfly" in [a.name for a in state.agents.values()]

def test_event_repository_hash_chain(temp_db):
    run_id = "test_run_101"
    temp_db.create_run(run_id, "Test Scenario")
    
    hash1 = temp_db.get_latest_event_hash(run_id)
    assert hash1 == "GENESIS"

    from emergence_lab.domain.events import Event
    e1 = Event(
        run_id=run_id,
        tick=0,
        event_type="test:event",
        actor_id="tester",
        payload={"msg": "hello"}
    )
    rec1 = temp_db.append_event(e1)
    assert rec1.previous_hash == "GENESIS"
    assert len(rec1.current_hash) == 64

def test_state_compiler_pid_resolution():
    world_def = FROZEN_BENCHMARK_WORLDS[0]
    state = build_frozen_world_state(world_def, "test_comp_run")
    compiler = StateCompiler(state)

    pid1 = compiler.get_pid("Aris Vance")
    assert pid1 == "p1"
    agent = compiler.resolve_pid("p1")
    assert agent is not None
    assert agent.name == "Aris Vance"

    compiled_text = compiler.compile_for_agent("panelist_1", [], max_ticks=3)
    assert "id: p1 (Aris Vance)" in compiled_text
    assert "VALID TARGET IDs: p2, p3" in compiled_text

def test_deterministic_verifier():
    verifier = DeterministicVerifier(valid_target_ids=["p2", "p3"])
    
    valid_turn = DialogueTurn(
        target_id="p2",
        claim="We must act empirically.",
        evidence="Data shows resilience.",
        challenge="Direct objection to p2.",
        question="What is the priority?"
    )
    v1 = verifier.verify(valid_turn)
    assert v1.is_valid is True

    invalid_target_turn = DialogueTurn(
        target_id="p88",
        claim="We must act empirically.",
        evidence="Data shows resilience.",
        challenge="Direct objection to p2.",
        question="What is the priority?"
    )
    v2 = verifier.verify(invalid_target_turn)
    assert v2.is_valid is False
    assert any("invalid_target_id" in issue for issue in v2.issues)

def test_governor_compact_v2_mode(temp_db):
    class MockV2Ollama:
        def chat_structured(self, sys_prompt, usr_prompt, response_schema=None, temperature=None):
            return {
                "target_id": "p2",
                "claim": "We must enforce empirical safety limits.",
                "evidence": "Systems engineering demonstrates failure modes under unconstrained growth.",
                "challenge": "p2 ignores practical resource limits.",
                "question": "How will rights be enforced if total system failure occurs?"
            }, InferenceResult(
                requested_model="mock_v2",
                actual_model="mock_v2",
                duration_ms=120.0
            )

    client = MockV2Ollama()
    world_def = FROZEN_BENCHMARK_WORLDS[0]
    state = build_frozen_world_state(world_def, "test_v2_run")
    temp_db.create_run(state.run_id, "V2 Benchmark Run")

    gov = Governor(temp_db, client, state, harness_mode="compact")
    prop, ev = gov.execute_agent_turn("panelist_1", max_ticks=3)

    assert prop.action.action_type == "speak"
    assert prop.telemetry is not None
    assert prop.telemetry.requested_model == "mock_v2"
    assert ev.telemetry is not None
    assert "Kaelen Voss" in prop.action.target_agent  # p2 resolved to Kaelen Voss
