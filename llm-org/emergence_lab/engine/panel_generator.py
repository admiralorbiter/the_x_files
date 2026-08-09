import json
from typing import List, Dict
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.domain.events import AgentState

DEFAULT_FALLBACK_PANEL = [
    {
        "name": "Dr. Aris Vance",
        "persona": "Empirical pragmatist and systems scientist who evaluates decisions based on quantifiable outcomes and systemic resilience.",
        "motive": "Demand verifiable evidence, challenge idealistic assumptions, and focus on practical long-term stability."
    },
    {
        "name": "Kaelen Voss",
        "persona": "Deontological philosopher focused on inviolable rights, justice, and moral duty regardless of utility.",
        "motive": "Uphold core moral principles, resist compromise on human rights, and expose utilitarian blind spots."
    },
    {
        "name": "Soren Kida",
        "persona": "Radical innovation theorist and accelerationist who sees crisis as an imperative for evolution and structural disruption.",
        "motive": "Advocate for transformative change, reject traditional constraints, and challenge fear-based caution."
    },
    {
        "name": "Mira Thorne",
        "persona": "Communitarian historian focused on social memory, cultural continuity, and community cohesion.",
        "motive": "Protect human relationships, preserve historical wisdom, and question technological or abstract fixes."
    }
]

def generate_panel(ollama_client: OllamaClient, scenario_text: str, num_panelists: int = 4) -> Dict[str, AgentState]:
    """Generates a diverse panel of thinkers for a given scenario using Ollama."""
    sys_prompt = "You are an expert organizational psychologist and curator of intellectual debates."
    usr_prompt = f"""Given this scenario:
"{scenario_text}"

Generate a panel of {num_panelists} distinct thinkers to debate this scenario.

CRITICAL REQUIREMENTS FOR EMRGENT DIALOGUE:
1. Diversity of Perspective: The panelists must have fundamentally opposing worldviews (e.g., pragmatist vs idealist vs traditionalist vs innovator).
2. Deep Specificity: Each panelist must have a clear background, a core conviction, AND an unexamined blind spot.
3. Tension Guarantee: At least one panelist must strongly disagree with the conventional approach to this problem.

Output JSON only matching this format:
{{
  "panelists": [
    {{
      "name": "Full Name or Title",
      "persona": "1-2 sentence background, epistemological style, and worldview.",
      "motive": "Their core conviction on this topic AND their specific blind spot."
    }}
  ]
}}
"""
    agents: Dict[str, AgentState] = {}

    try:
        res = ollama_client.chat_json(sys_prompt, usr_prompt)
        panel_data = res.get("panelists", [])
        if isinstance(panel_data, list) and len(panel_data) > 0:
            for idx, p in enumerate(panel_data[:num_panelists], start=1):
                agent_id = f"panelist_{idx}"
                name = p.get("name", f"Panelist {idx}")
                persona = p.get("persona", "Thoughtful seeker of truth.")
                motive = p.get("motive", "Engage in meaningful dialogue and offer unique insight.")
                agents[agent_id] = AgentState(
                    agent_id=agent_id,
                    name=name,
                    persona=persona,
                    motive=motive,
                    location="The Forum"
                )
            return agents
    except Exception as e:
        print(f"   [Panel Gen] Warning: Could not generate panel via LLM ({e}). Using default fallback panel.")

    # Fallback if LLM parsing fails
    for idx, p in enumerate(DEFAULT_FALLBACK_PANEL[:num_panelists], start=1):
        agent_id = f"panelist_{idx}"
        agents[agent_id] = AgentState(
            agent_id=agent_id,
            name=p["name"],
            persona=p["persona"],
            motive=p["motive"],
            location="The Forum"
        )
    return agents
