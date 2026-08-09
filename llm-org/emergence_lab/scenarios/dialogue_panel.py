import uuid
from typing import Optional
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.domain.events import WorldState, LocationState
from emergence_lab.engine.topics_v2 import generate_scenario
from emergence_lab.engine.panel_generator import generate_panel

def build_dialogue_panel_scenario(
    ollama_client: OllamaClient,
    run_id: str = "",
    num_panelists: int = 4,
    domain: str = "",
    lens: str = ""
) -> WorldState:
    if not run_id:
        run_id = f"run_dialogue_{str(uuid.uuid4())[:8]}"

    # Step 1: Generate Scenario
    scenario_text, domain_used, lens_used = generate_scenario(ollama_client, domain=domain, lens=lens)

    # Step 2: Generate Panel based on Scenario
    agents = generate_panel(ollama_client, scenario_text=scenario_text, num_panelists=num_panelists)

    # Step 3: Single location ("The Forum")
    locations = {
        "The Forum": LocationState(
            name="The Forum",
            description="A serene central chamber designed for focused, unimpeded dialogue and synthesis among thinkers.",
            connected_locations=[]
        )
    }

    return WorldState(
        run_id=run_id,
        tick=0,
        scenario_text=scenario_text,
        locations=locations,
        agents=agents
    )
