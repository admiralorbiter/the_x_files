import uuid
from emergence_lab.domain.events import WorldState, LocationState, AgentState

def build_socratic_academy_scenario(run_id: str = "") -> WorldState:
    if not run_id:
        run_id = f"run_socratic_{str(uuid.uuid4())[:8]}"

    locations = {
        "Stoa of Paradoxes": LocationState(
            name="Stoa of Paradoxes",
            description="A shaded marble colonnade where philosophers gather to debate the nature of mind, reality, and consciousness.",
            resources={"Axioms": 10, "Aporia": 15},
            connected_locations=["Academy of Ethics", "Dialectic Grove"]
        ),
        "Academy of Ethics": LocationState(
            name="Academy of Ethics",
            description="A courtyard dedicated to inquiries on justice, virtue, governance, and the good life.",
            resources={"Axioms": 12, "Elenchus": 8},
            connected_locations=["Stoa of Paradoxes", "Dialectic Grove"]
        ),
        "Dialectic Grove": LocationState(
            name="Dialectic Grove",
            description="A quiet grove of olive trees where thinkers test hypotheses through rigorous cross-examination.",
            resources={"Aporia": 10, "Elenchus": 12},
            connected_locations=["Stoa of Paradoxes", "Academy of Ethics"]
        )
    }

    agents = {
        "philosopher_1": AgentState(
            agent_id="philosopher_1",
            name="Socrates the Gadfly",
            persona="Relentless seeker of wisdom who uses questioning to expose ignorance and examine assumptions.",
            motive="Expose unexamined assumptions, uncover Aporia (puzzles), and spawn disciple sub-agents to question dogma.",
            location="Stoa of Paradoxes",
            resources={"Aporia": 4}
        ),
        "philosopher_2": AgentState(
            agent_id="philosopher_2",
            name="Plato the Systematizer",
            persona="Visionary philosopher aiming to discover objective forms and harmonize ideals into lasting institutions.",
            motive="Synthesize Axioms, establish an Academy School of Thought, and record foundational Socratic Dialogues.",
            location="Academy of Ethics",
            resources={"Axioms": 3}
        ),
        "philosopher_3": AgentState(
            agent_id="philosopher_3",
            name="Heraclitus the Paradoxer",
            persona="Philosopher of change who believes truth emerges through dialectical tension and perpetual flux.",
            motive="Challenge rigid Axioms, engage in Elenchus debates, and author treatises on the harmony of opposites.",
            location="Dialectic Grove",
            resources={"Elenchus": 3}
        )
    }

    return WorldState(
        run_id=run_id,
        tick=0,
        locations=locations,
        agents=agents
    )
