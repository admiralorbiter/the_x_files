import os
import pytest
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.governor import Governor
from emergence_lab.scenarios.society_micro import build_micro_society_scenario
from emergence_lab.scenarios.socratic_academy import build_socratic_academy_scenario
from emergence_lab.domain.events import AgentAction, AgentTurnProposal

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_emergence.db")
    return EventRepository(db_path=db_file)

def test_socratic_scenario_build():
    state = build_socratic_academy_scenario("test_socratic_run")
    assert len(state.agents) == 3
    assert len(state.locations) == 3
    assert "Socrates the Gadfly" in [a.name for a in state.agents.values()]

def test_event_repository_hash_chain(temp_db):
    run_id = "test_run_101"
    temp_db.create_run(run_id, "Test Scenario")
    
    # Verify initial genesis hash
    hash1 = temp_db.get_latest_event_hash(run_id)
    assert hash1 == "GENESIS"

    # Append first event
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

    # Append second event
    e2 = Event(
        run_id=run_id,
        tick=1,
        event_type="test:event2",
        actor_id="tester",
        payload={"msg": "world"}
    )
    rec2 = temp_db.append_event(e2)
    assert rec2.previous_hash == rec1.current_hash
    assert len(rec2.current_hash) == 64

def test_governor_action_application(temp_db):
    state = build_micro_society_scenario("test_run_202")
    temp_db.create_run(state.run_id, "Micro Scenario")
    client = OllamaClient()
    governor = Governor(temp_db, client, state)

    agent = state.agents["agent_1"]
    
    # Test Gather
    gather_act = AgentAction(action_type="gather", resource_type="Parchment", resource_amount=3, rationale="Gather parchment")
    res = governor.apply_action(agent, gather_act)
    assert res["status"] == "applied"
    assert agent.resources["Parchment"] == 6

    # Test Move
    move_act = AgentAction(action_type="move", target_location="Whisper Market", rationale="Head to market")
    res_move = governor.apply_action(agent, move_act)
    assert res_move["status"] == "applied"
    assert agent.location == "Whisper Market"

    # Test Spawn Sub-Agent
    spawn_act = AgentAction(
        action_type="spawn_agent",
        sub_agent_name="Scribe_Alpha",
        sub_agent_motive="Copy parchment records",
        rationale="Delegate copying"
    )
    res_spawn = governor.apply_action(agent, spawn_act)
    assert res_spawn["status"] == "applied"
    assert len(state.agents) == 4
    sub = next(a for a in state.agents.values() if a.name == "Scribe_Alpha")
    assert sub.parent_agent_id == agent.agent_id

    # Test Create Institution
    inst_act = AgentAction(
        action_type="create_institution",
        institution_name="Scribes Guild",
        institution_charter="Protect knowledge",
        rationale="Form guild"
    )
    res_inst = governor.apply_action(agent, inst_act)
    assert res_inst["status"] == "applied"
    assert len(state.institutions) == 1
