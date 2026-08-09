import argparse
import sys
import time
import io
from emergence_lab.config import default_config
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.governor import Governor
from emergence_lab.scenarios.society_micro import build_micro_society_scenario
from emergence_lab.scenarios.socratic_academy import build_socratic_academy_scenario

# Ensure sys.stdout handles UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_simulation(ticks: int = 5, model_name: str = default_config.default_model, db_path: str = default_config.db_path, scenario: str = "socratic"):
    if scenario.lower() == "socratic":
        world_state = build_socratic_academy_scenario()
        scenario_title = "SOCRATIC ACADEMY: THE DIALECTIC GROVE"
    else:
        world_state = build_micro_society_scenario()
        scenario_title = "SOCIETY LAB: THE WHISPERING ENCLAVE"

    print("=" * 70)
    print(f" EMERGENCE LAB -- {scenario_title}")
    print("=" * 70)
    print(f" -> Model: {model_name}")
    print(f" -> DB Path: {db_path}")
    print(f" -> Total Ticks: {ticks}")
    print("-" * 70, flush=True)

    repo = EventRepository(db_path=db_path)
    client = OllamaClient(model=model_name)
    
    repo.create_run(world_state.run_id, scenario_name=scenario_title)
    governor = Governor(repository=repo, ollama_client=client, world_state=world_state)

    for tick in range(1, ticks + 1):
        print(f"\n--- TICK {world_state.tick + 1} ---", flush=True)
        shock = governor.get_procedural_shock()
        if shock:
            print(f"   {shock}", flush=True)
        
        # Schedule active agents
        active_agents = list(governor.state.agents.values())
        for agent in active_agents:
            if agent.status != "active":
                continue
            
            print(f"\n[Thinker] {agent.name} (Location: {agent.location})", flush=True)
            try:
                proposal, event = governor.execute_agent_turn(agent.agent_id)
                print(f"   Thoughts:  {proposal.thoughts}", flush=True)
                print(f"   Action:    {proposal.action.action_type.upper()}", flush=True)
                if proposal.action.action_type == "speak" and proposal.action.message:
                    target = proposal.action.target_agent or "all"
                    print(f"   💬 Speech (to {target}): \"{proposal.action.message}\"", flush=True)
                elif proposal.action.action_type == "record_artifact" and proposal.action.artifact_title:
                    print(f"   📜 Created Artifact: '{proposal.action.artifact_title}'", flush=True)
                elif proposal.action.action_type == "create_institution" and proposal.action.institution_name:
                    print(f"   🏛️ Founded School: '{proposal.action.institution_name}'", flush=True)
                elif proposal.action.action_type == "spawn_agent" and proposal.action.sub_agent_name:
                    print(f"   🌱 Spawned Disciple: '{proposal.action.sub_agent_name}'", flush=True)
                print(f"   Rationale: {proposal.action.rationale}", flush=True)
                print(f"   Hash:      {event.current_hash[:12]}...", flush=True)
            except Exception as e:
                print(f"   Warning: Error during turn execution: {e}", flush=True)
        
        governor.advance_tick()
        time.sleep(0.3)

    print("\n" + "=" * 70)
    print(" SIMULATION COMPLETE -- EMERGENT DIALECTIC SUMMARY")
    print("=" * 70)
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
    run_parser.add_argument("--ticks", type=int, default=5, help="Number of ticks to run")
    run_parser.add_argument("--model", type=str, default=default_config.default_model, help="Ollama model name")
    run_parser.add_argument("--db", type=str, default=default_config.db_path, help="SQLite database file")
    run_parser.add_argument("--scenario", type=str, default="socratic", choices=["socratic", "micro"], help="Scenario selection (socratic or micro)")

    args = parser.parse_args()

    if args.command == "run":
        run_simulation(ticks=args.ticks, model_name=args.model, db_path=args.db, scenario=args.scenario)
    else:
        run_parser.print_help()

if __name__ == "__main__":
    main()
