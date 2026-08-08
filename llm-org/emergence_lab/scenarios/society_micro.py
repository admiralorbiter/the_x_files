import uuid
from emergence_lab.domain.events import WorldState, LocationState, AgentState

def build_micro_society_scenario(run_id: str = "") -> WorldState:
    if not run_id:
        run_id = f"run_micro_{str(uuid.uuid4())[:8]}"

    locations = {
        "High Observatory": LocationState(
            name="High Observatory",
            description="A high stone tower looking out over drifting cloudscapes where scholars observe celestial anomalies.",
            resources={"Aether": 12, "Parchment": 5},
            connected_locations=["Whisper Market"]
        ),
        "Whisper Market": LocationState(
            name="Whisper Market",
            description="A subterranean bazaar where merchants trade parchment, rare artifacts, and rumors.",
            resources={"Parchment": 25, "Echo Crystals": 8},
            connected_locations=["High Observatory", "Crystal Vault"]
        ),
        "Crystal Vault": LocationState(
            name="Crystal Vault",
            description="A glowing crystal cavern where resonant stones store atmospheric and acoustic memories.",
            resources={"Echo Crystals": 15, "Aether": 6},
            connected_locations=["Whisper Market"]
        )
    }

    agents = {
        "agent_1": AgentState(
            agent_id="agent_1",
            name="Aurelius the Archivist",
            persona="An obsessive scholar who fears knowledge will decay unless preserved in written artifacts.",
            motive="Gather Parchment and write permanent historical artifacts of every event.",
            location="High Observatory",
            resources={"Parchment": 3}
        ),
        "agent_2": AgentState(
            agent_id="agent_2",
            name="Lyra the Merchant",
            persona="A pragmatic trade broker seeking to establish commerce networks and institutions.",
            motive="Trade resources, acquire Echo Crystals and Aether, and create trade councils.",
            location="Whisper Market",
            resources={"Echo Crystals": 2}
        ),
        "agent_3": AgentState(
            agent_id="agent_3",
            name="Vaelen the Delegate",
            persona="A visionary explorer who creates sub-agents to extend influence across all regions.",
            motive="Spawn sub-agents to explore every connected region and establish a unifying covenant.",
            location="Crystal Vault",
            resources={"Aether": 2}
        )
    }

    return WorldState(
        run_id=run_id,
        tick=0,
        locations=locations,
        agents=agents
    )
