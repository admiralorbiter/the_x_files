import json
from typing import List, Dict
from emergence_lab.adapters.ollama_client import OllamaClient
from emergence_lab.domain.events import AgentState
from emergence_lab.engine.dialogue_scaffolds import DIALECTICAL_ROLES

DEFAULT_FALLBACK_PANEL = [
    {
        "name": "Aris Vance",
        "persona": "Empirical pragmatist who evaluates decisions based on quantifiable outcomes and systemic resilience.",
        "motive": "Demand verifiable evidence and focus on practical long-term stability.",
        "dialectical_role": "ADVOCATE",
        "stance": "Deploy the system under strict, measured empirical boundaries."
    },
    {
        "name": "Kaelen Voss",
        "persona": "Deontological philosopher focused on inviolable human rights and agency.",
        "motive": "Uphold core moral principles and expose utilitarian blind spots.",
        "dialectical_role": "CRITIC",
        "stance": "Halt deployment; human agency cannot be traded for technological convenience."
    },
    {
        "name": "Soren Kida",
        "persona": "Radical innovation theorist who sees disruption as an evolutionary imperative.",
        "motive": "Advocate for transformative evolution and reject fear-based caution.",
        "dialectical_role": "WILDCARD",
        "stance": "Accelerate deployment completely; friction and crisis are necessary for human growth."
    },
    {
        "name": "Mira Thorne",
        "persona": "Communitarian historian focused on social memory and cultural continuity.",
        "motive": "Protect human relationships and question technological fixes.",
        "dialectical_role": "SYNTHESIZER",
        "stance": "Seek a localized, community-controlled framework rather than central deployment."
    }
]

ROLE_KEYS = ["ADVOCATE", "CRITIC", "WILDCARD", "SYNTHESIZER"]

def generate_panel(ollama_client: OllamaClient, scenario_text: str, num_panelists: int = 4) -> Dict[str, AgentState]:
    """Generates a diverse panel of thinkers with explicit dialectical roles and short names using Ollama."""
    sys_prompt = "You are an expert organizational psychologist and curator of intellectual debates."
    usr_prompt = f"""Given this scenario:
"{scenario_text}"

Generate a panel of {num_panelists} distinct thinkers to debate this scenario.

CRITICAL REQUIREMENTS:
1. Short, Punchy Names: Each panelist must have a clean, 2-word name (e.g. "Ren Vance", "Kaelen Voss", "Elena Cruz"). NO long titles or complex names.
2. Dialectical Roles: Assign each panelist one of these exact roles: {', '.join(ROLE_KEYS[:num_panelists])}.
3. Fundamentally Opposing Stances: Each panelist must take an unyielding, specific stance on the scenario.
4. Deep Specificity: Each panelist must have a background, a driving motive, and a clear blind spot.

Output JSON only matching this format:
{{
  "panelists": [
    {{
      "name": "Short Name",
      "dialectical_role": "ADVOCATE|CRITIC|WILDCARD|SYNTHESIZER",
      "stance": "Their exact position on the scenario in 1 sentence",
      "persona": "1-2 sentence background and worldview.",
      "motive": "Core conviction and specific blind spot."
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
                # Ensure name is not too long
                if len(name.split()) > 2:
                    name = " ".join(name.split()[:2])
                
                role = p.get("dialectical_role", ROLE_KEYS[(idx-1) % len(ROLE_KEYS)])
                if role not in ROLE_KEYS:
                    role = ROLE_KEYS[(idx-1) % len(ROLE_KEYS)]
                
                stance = p.get("stance", "Maintain an authentic perspective on this scenario.")
                persona = p.get("persona", "Thoughtful seeker of truth.")
                motive = p.get("motive", "Engage in meaningful dialogue and offer unique insight.")
                
                agents[agent_id] = AgentState(
                    agent_id=agent_id,
                    name=name,
                    persona=persona,
                    motive=motive,
                    location="The Forum",
                    dialectical_role=role,
                    stance=stance
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
            location="The Forum",
            dialectical_role=p["dialectical_role"],
            stance=p["stance"]
        )
    return agents
