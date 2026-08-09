"""Frozen Benchmark Worlds for Controlled Emergence Lab Experiments.

Pre-curated scenarios and panelist setups to ensure identical initial conditions
across all model and harness mode evaluations.
"""

from typing import List, Dict, Any
from emergence_lab.domain.events import WorldState, AgentState, LocationState

FROZEN_BENCHMARK_WORLDS: List[Dict[str, Any]] = [
    {
        "id": "world_01_quantum_ai",
        "scenario": "[Quantum Leap Dilemma] Quantum computing enables an AI system capable of solving complex global crises, but requires granting it total decision-making authority over human governance. Should humanity deploy the AI to ensure survival or prohibit it to protect human autonomy?",
        "panelists": [
            {
                "id": "panelist_1",
                "name": "Aris Vance",
                "dialectical_role": "ADVOCATE",
                "persona": "Empirical pragmatist and systems scientist.",
                "motive": "Deploy the system under strict empirical risk controls to ensure survival.",
                "stance": "Deploy the system under strict, measured empirical boundaries."
            },
            {
                "id": "panelist_2",
                "name": "Kaelen Voss",
                "dialectical_role": "CRITIC",
                "persona": "Deontological moral philosopher.",
                "motive": "Uphold core moral principles and human agency above utility.",
                "stance": "Halt deployment; human agency cannot be traded for technological convenience."
            },
            {
                "id": "panelist_3",
                "name": "Soren Kida",
                "dialectical_role": "WILDCARD",
                "persona": "Radical innovation theorist and accelerationist.",
                "motive": "Promote disruptive evolution and reject fear-based caution.",
                "stance": "Accelerate deployment completely; friction and crisis are necessary for human growth."
            }
        ]
    },
    {
        "id": "world_02_memory_transfer",
        "scenario": "[Memory & Synthetic Continuation] Technological transfer allows complete memory and consciousness migration into synthetic bodies, granting functional immortality but requiring the destruction of the biological form. Should individuals be permitted to undergo the procedure?",
        "panelists": [
            {
                "id": "panelist_1",
                "name": "Elena Cruz",
                "dialectical_role": "ADVOCATE",
                "persona": "Transhumanist physician and cognitive scientist.",
                "motive": "Preserve human identity and knowledge beyond biological decay.",
                "stance": "Allow voluntary migration under strict medical and identity verification."
            },
            {
                "id": "panelist_2",
                "name": "Marcus Hale",
                "dialectical_role": "CRITIC",
                "persona": "Bioethicist and organic continuity scholar.",
                "motive": "Protect organic life integrity and prevent social stratification.",
                "stance": "Prohibit synthetic migration to prevent the destruction of biological humanity."
            },
            {
                "id": "panelist_3",
                "name": "Talia Ren",
                "dialectical_role": "WILDCARD",
                "persona": "Existential sociologist.",
                "motive": "Expose the hubris of digital immortality and question post-human identity.",
                "stance": "Reframe the problem around community continuity rather than individual survival."
            }
        ]
    },
    {
        "id": "world_03_scarcity_rationing",
        "scenario": "[Morality under Extreme Scarcity] Critical ecological collapse forces planetary resource rationing. Algorithms can maximize survival probability but require sacrificing equal access rights for vulnerable populations. Should society follow algorithmic utility or uphold equal rights?",
        "panelists": [
            {
                "id": "panelist_1",
                "name": "Darius Cole",
                "dialectical_role": "ADVOCATE",
                "persona": "Resource optimization engineer.",
                "motive": "Maximize long-term systemic survival using verifiable resource modeling.",
                "stance": "Implement algorithmic allocation to prevent total collapse."
            },
            {
                "id": "panelist_2",
                "name": "Lyra Thorne",
                "dialectical_role": "CRITIC",
                "persona": "Human rights advocate and historian.",
                "motive": "Guarantee equal protection and prevent algorithmic triage.",
                "stance": "Mandate equal distribution regardless of algorithmic efficiency."
            },
            {
                "id": "panelist_3",
                "name": "Zane Kross",
                "dialectical_role": "WILDCARD",
                "persona": "Post-scarcity theorist.",
                "motive": "Disrupt consumption structures rather than managing scarcity.",
                "stance": "Reject rationing framing entirely; force immediate structural transformation."
            }
        ]
    }
]

def build_frozen_world_state(world_dict: Dict[str, Any], run_id: str) -> WorldState:
    """Builds a deterministic WorldState from a frozen benchmark definition."""
    state = WorldState(
        run_id=run_id,
        scenario_text=world_dict["scenario"],
        locations={
            "The Forum": LocationState(
                name="The Forum",
                description="Central Chamber of Dialectic Inquiry"
            )
        }
    )
    for p in world_dict["panelists"]:
        agent = AgentState(
            agent_id=p["id"],
            name=p["name"],
            persona=p["persona"],
            motive=p["motive"],
            location="The Forum",
            dialectical_role=p["dialectical_role"],
            stance=p["stance"]
        )
        state.agents[p["id"]] = agent
    return state
