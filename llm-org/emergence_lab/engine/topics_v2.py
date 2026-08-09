import random
from typing import Tuple
from emergence_lab.adapters.ollama_client import OllamaClient

DOMAINS = [
    "technology", "justice", "knowledge", "identity", "power",
    "nature", "consciousness", "community", "truth", "freedom",
    "art", "morality", "scarcity", "progress", "memory"
]

LENSES = [
    "scarcity", "conflict", "discovery", "collapse", "first contact",
    "betrayal", "abundance", "revolution", "paradox", "inheritance",
    "transformation", "dilemma", "isolation", "hubris", "synthesis"
]

def generate_scenario_seed() -> Tuple[str, str]:
    domain = random.choice(DOMAINS)
    lens = random.choice(LENSES)
    while lens == domain:
        lens = random.choice(LENSES)
    return domain, lens

def generate_scenario(ollama_client: OllamaClient, domain: str = "", lens: str = "") -> Tuple[str, str, str]:
    """Generates a scenario using domain + lens seed and Ollama. Returns (scenario_text, domain, lens)."""
    if not domain or not lens:
        domain, lens = generate_scenario_seed()

    sys_prompt = "You are a creative philosopher and narrative generator for Emergence Lab."
    usr_prompt = f"""Given the intersection of the domain '{domain}' and the lens '{lens}', construct a compelling, concrete scenario for a panel of thinkers to debate.

REQUIREMENTS:
1. Provide a realistic or speculative situation with high stakes and no obvious right answer.
2. It should be 2-4 sentences long.
3. It must provoke fundamental debate across ethics, strategy, epistemology, or human values.

Output JSON only in this exact format:
{{
  "scenario_title": "Short title",
  "scenario_text": "The detailed scenario text..."
}}
"""
    try:
        res = ollama_client.chat_json(sys_prompt, usr_prompt)
        text = res.get("scenario_text") or res.get("scenario", "")
        title = res.get("scenario_title") or f"{domain.capitalize()} & {lens.capitalize()}"
        if text:
            return f"[{title}] {text}", domain, lens
    except Exception as e:
        print(f"   [Topic Gen] Warning: Could not generate scenario via LLM ({e}). Using template fallback.")

    fallback_text = f"[{domain.capitalize()} under {lens.capitalize()}] A critical juncture has been reached where principles of {domain} clash directly with the reality of {lens}. The panel must determine the immediate path forward and the foundational principles that justify it."
    return fallback_text, domain, lens
