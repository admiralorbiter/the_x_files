import argparse
import sys
import time
import io
import json
from emergence_lab.config import default_config
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.governor import Governor
from emergence_lab.scenarios.society_micro import build_micro_society_scenario
from emergence_lab.scenarios.socratic_academy import build_socratic_academy_scenario
from emergence_lab.scenarios.dialogue_panel import build_dialogue_panel_scenario

# Ensure sys.stdout handles UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_simulation(
    ticks: int = 5,
    model_name: str = default_config.default_model,
    db_path: str = default_config.db_path,
    scenario: str = "dialogue",
    panelists: int = 4,
    harness: str = "full"
):
    client = OllamaClient(model=model_name)
    repo = EventRepository(db_path=db_path)

    if scenario.lower() == "dialogue":
        print("⚡ Generating scenario topic and establishing panel of thinkers via Ollama...")
        world_state = build_dialogue_panel_scenario(ollama_client=client, num_panelists=panelists)
        scenario_title = "EMERGENT DIALECTIC FORUM"
    elif scenario.lower() == "socratic":
        world_state = build_socratic_academy_scenario()
        scenario_title = "SOCRATIC ACADEMY: THE DIALECTIC GROVE"
    else:
        world_state = build_micro_society_scenario()
        scenario_title = "SOCIETY LAB: THE WHISPERING ENCLAVE"

    print("=" * 70)
    print(f" EMERGENCE LAB -- {scenario_title}")
    print("=" * 70)
    print(f" -> Model: {model_name}")
    print(f" -> Harness Mode: {harness.upper()}")
    print(f" -> DB Path: {db_path}")
    print(f" -> Total Rounds/Ticks: {ticks}")
    if world_state.scenario_text:
        print("-" * 70)
        print(f" 📜 GENERATED SCENARIO:\n {world_state.scenario_text}")
        print("-" * 70)
        print(" 🏛️ GENERATED PANELISTS:")
        for a in world_state.agents.values():
            role_str = f" [{a.dialectical_role}]" if a.dialectical_role else ""
            stance_str = f"\n     - Stance: {a.stance}" if a.stance else ""
            print(f"   * {a.name}{role_str}\n     - Background: {a.persona}\n     - Driving Motive: {a.motive}{stance_str}\n")
    print("-" * 70, flush=True)

    repo.create_run(world_state.run_id, scenario_name=scenario_title)
    governor = Governor(repository=repo, ollama_client=client, world_state=world_state, harness_mode=harness)

    for tick in range(1, ticks + 1):
        round_label = f"ROUND {world_state.tick + 1} OF {ticks}" if world_state.scenario_text else f"TICK {world_state.tick + 1}"
        print(f"\n--- {round_label} ---", flush=True)
        
        if not world_state.scenario_text:
            shock = governor.get_procedural_shock()
            if shock:
                print(f"   {shock}", flush=True)
        
        # Check moderator pass between middle rounds
        if world_state.scenario_text and world_state.tick > 0:
            provocation = governor.run_moderator_pass()
            if provocation:
                print(f"\n ⚡ [MODERATOR PROVOCATION]:\n \"{provocation}\"\n", flush=True)

        active_agents = list(governor.state.agents.values())
        for agent in active_agents:
            if agent.status != "active":
                continue
            
            role_tag = f" ({agent.dialectical_role})" if agent.dialectical_role else ""
            print(f"\n[Panelist] {agent.name}{role_tag}", flush=True)
            try:
                proposal, event = governor.execute_agent_turn(agent.agent_id, max_ticks=ticks)
                print(f"   💭 Internal Reflection: {proposal.thoughts}", flush=True)
                act_type = proposal.action.action_type
                
                if act_type in ["speak", "synthesize"]:
                    target = proposal.action.target_agent or "all"
                    icon = "💬 Speech" if act_type == "speak" else "📜 Synthesis"
                    print(f"   {icon} (to {target}):\n   \"{proposal.action.message}\"", flush=True)
                elif act_type == "record_artifact" and proposal.action.artifact_title:
                    print(f"   📜 Created Artifact: '{proposal.action.artifact_title}'", flush=True)
                elif act_type == "create_institution" and proposal.action.institution_name:
                    print(f"   🏛️ Founded School: '{proposal.action.institution_name}'", flush=True)
                elif act_type == "spawn_agent" and proposal.action.sub_agent_name:
                    print(f"   🌱 Spawned Disciple: '{proposal.action.sub_agent_name}'", flush=True)
                
                print(f"   Rationale: {proposal.action.rationale}", flush=True)
                print(f"   Event Hash: {event.current_hash[:12]}...", flush=True)
            except Exception as e:
                print(f"   Warning: Error during turn execution: {e}", flush=True)
        
        governor.advance_tick()
        time.sleep(0.3)

    print("\n" + "=" * 70)
    print(" SIMULATION COMPLETE -- EMERGENT DIALECTIC SUMMARY")
    print("=" * 70)
    
    if world_state.scenario_text:
        print(f"\n 📜 SCENARIO: {world_state.scenario_text}")
        print("\n 💬 PANEL STATEMENTS & SYNTHESIS:")
        all_events = repo.get_events(world_state.run_id)
        
        speech_lengths = []
        question_count = 0
        moderator_count = 0
        
        for ev in all_events:
            ev_type = ev.get("event_type", "")
            actor = ev.get("actor_id", "")
            payload = json.loads(ev["payload"]) if isinstance(ev["payload"], str) else ev["payload"]
            
            if ev_type == "action:speak":
                msg = payload.get("speech", {}).get("message", "")
                speech_lengths.append(len(msg))
                if "?" in msg:
                    question_count += 1
                print(f"\n [{actor}]:\n \"{msg}\"")
            elif ev_type == "action:synthesize":
                msg = payload.get("synthesis", {}).get("message", "")
                speech_lengths.append(len(msg))
                if "?" in msg:
                    question_count += 1
                print(f"\n 🏆 [{actor} FINAL VERDICT/SYNTHESIS]:\n \"{msg}\"")
            elif ev_type == "event:moderator_provocation":
                moderator_count += 1
                prov = payload.get("provocation", "")
                print(f"\n ⚡ [MODERATOR PROVOCATION]:\n \"{prov}\"")

        avg_length = sum(speech_lengths) / len(speech_lengths) if speech_lengths else 0
        print("\n" + "-" * 70)
        print(" 📊 DIALECTIC QUALITY METRICS:")
        print(f"   * Average Speech Length: {avg_length:.1f} characters")
        print(f"   * Probing Questions Posed: {question_count}")
        print(f"   * Moderator Interventions: {moderator_count}")
        print(f"   * Harness Mode Active: {harness.upper()}")
        print("-" * 70)
    else:
        print(f" -> Total Active Thinkers: {len(governor.state.agents)}")
        for a in governor.state.agents.values():
            parent_str = f" (Mentored by {a.parent_agent_id})" if a.parent_agent_id else ""
            print(f"   * {a.name}{parent_str} @ {a.location} | Concepts: {a.resources}")

        print(f"\n -> Philosophical Schools Established: {len(governor.state.institutions)}")
        for inst in governor.state.institutions.values():
            print(f"   [School] '{inst.name}' by {inst.creator_id}: {inst.charter}")

        print(f"\n -> Socratic Dialogues & Treatises Authored: {len(governor.state.artifacts)}")
        for art in governor.state.artifacts.values():
            print(f"   [Dialogue] '{art.title}' by {art.author_id}: {art.content[:70]}...")
    
    print("\nEvents persisted and committed to SQLite WAL database.")
    print("=" * 70, flush=True)

def main():
    parser = argparse.ArgumentParser(description="Emergence Lab Simulation CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an Emergence Lab simulation")
    run_parser.add_argument("--ticks", type=int, default=4, help="Number of dialogue rounds/ticks to run")
    run_parser.add_argument("--model", type=str, default=default_config.default_model, help="Ollama model name")
    run_parser.add_argument("--db", type=str, default=default_config.db_path, help="SQLite database file")
    run_parser.add_argument("--scenario", type=str, default="dialogue", choices=["dialogue", "socratic", "micro"], help="Scenario selection")
    run_parser.add_argument("--panelists", type=int, default=4, help="Number of generated panelists for dialogue scenario")
    run_parser.add_argument("--harness", type=str, default="full", choices=["full", "light", "off"], help="Dialogue harness mode (full, light, off)")

    args = parser.parse_args()

    if args.command == "run":
        run_simulation(
            ticks=args.ticks,
            model_name=args.model,
            db_path=args.db,
            scenario=args.scenario,
            panelists=args.panelists,
            harness=args.harness
        )
    else:
        run_parser.print_help()

if __name__ == "__main__":
    main()
