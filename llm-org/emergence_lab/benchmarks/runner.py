"""Emergence Lab Benchmark Matrix Runner.

Executes controlled matrix experiments across models, harness modes, and frozen worlds.
"""

import argparse
import json
import sys
import io
import time
from typing import List
from emergence_lab.adapters.db import EventRepository
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.engine.governor import Governor
from emergence_lab.benchmarks.frozen_worlds import FROZEN_BENCHMARK_WORLDS, build_frozen_world_state
from emergence_lab.benchmarks.evaluator import evaluate_run

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_benchmark_matrix(
    models: List[str],
    modes: List[str],
    world_indices: List[int],
    ticks: int = 3,
    db_path: str = "emergence_benchmarks.db"
):
    repo = EventRepository(db_path=db_path)
    results = []

    print("=" * 75)
    print(" 🧪 EMERGENCE LAB V2 BENCHMARK RUNNER")
    print("=" * 75)
    print(f" -> Models: {', '.join(models)}")
    print(f" -> Modes: {', '.join(modes)}")
    print(f" -> Frozen Worlds: {len(world_indices)}")
    print(f" -> Ticks per Run: {ticks}")
    print("=" * 75, flush=True)

    for model_name in models:
        client = OllamaClient(model=model_name)
        for mode in modes:
            for w_idx in world_indices:
                world_def = FROZEN_BENCHMARK_WORLDS[w_idx % len(FROZEN_BENCHMARK_WORLDS)]
                run_id = f"bench_{model_name.replace(':', '_')}_{mode}_w{w_idx}_{int(time.time())}"
                world_state = build_frozen_world_state(world_def, run_id)
                
                print(f"\n⚡ Running Model [{model_name}] | Mode [{mode.upper()}] | World [{world_def['id']}]...", flush=True)
                repo.create_run(run_id, scenario_name=world_def['id'])
                governor = Governor(repository=repo, ollama_client=client, world_state=world_state, harness_mode=mode)

                for tick in range(1, ticks + 1):
                    for agent in list(governor.state.agents.values()):
                        try:
                            prop, ev = governor.execute_agent_turn(agent.agent_id, max_ticks=ticks)
                        except Exception as e:
                            print(f"   Warning: turn error: {e}", flush=True)
                    governor.advance_tick()

                # Evaluate run telemetry
                events = repo.get_events(run_id)
                metrics = evaluate_run(events, model_name=model_name, harness_mode=mode)
                summary = metrics.compute_summary()
                results.append(summary)

                print(f"   ✓ Completed | Chars: {summary['avg_speech_length_chars']} | Fidelity: {summary['target_fidelity_pct']}% | Duration: {summary['total_duration_sec']}s | Efficiency Ratio: {summary['compute_efficiency_ratio']}")

    print("\n" + "=" * 75)
    print(" 📊 BENCHMARK MATRIX SUMMARY RESULTS")
    print("=" * 75)
    print(json.dumps(results, indent=2))
    print("=" * 75, flush=True)

    return results

def main():
    parser = argparse.ArgumentParser(description="Emergence Lab Benchmark Runner")
    parser.add_argument("--models", type=str, default="qwen2.5:3b", help="Comma-separated model names")
    parser.add_argument("--modes", type=str, default="compact,raw", help="Comma-separated harness modes (compact, light, raw)")
    parser.add_argument("--worlds", type=str, default="0", help="Comma-separated frozen world indices (0, 1, 2)")
    parser.add_argument("--ticks", type=int, default=2, help="Ticks per run")
    parser.add_argument("--db", type=str, default="emergence_benchmarks.db", help="SQLite database path")

    args = parser.parse_args()

    models_list = [m.strip() for m in args.models.split(",") if m.strip()]
    modes_list = [m.strip() for m in args.modes.split(",") if m.strip()]
    worlds_list = [int(w.strip()) for w in args.worlds.split(",") if w.strip().isdigit()]

    run_benchmark_matrix(
        models=models_list,
        modes=modes_list,
        world_indices=worlds_list,
        ticks=args.ticks,
        db_path=args.db
    )

if __name__ == "__main__":
    main()
