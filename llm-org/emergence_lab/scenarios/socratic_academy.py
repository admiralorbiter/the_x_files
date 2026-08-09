import uuid
from emergence_lab.domain.events import WorldState, LocationState, AgentState

def build_socratic_academy_scenario(run_id: str = "") -> WorldState:
    if not run_id:
        run_id = f"run_socratic_{str(uuid.uuid4())[:8]}"

    locations = {
        "Stoa of Paradoxes": LocationState(
            name="Stoa of Paradoxes",
            description="A grand marble colonnade where thinkers gather to debate the nature of truth, mind, and reality.",
            resources={"Axioms": 15, "Aporia": 20},
            connected_locations=["Academy of Ethics", "Dialectic Grove"]
        ),
        "Academy of Ethics": LocationState(
            name="Academy of Ethics",
            description="A shaded courtyard dedicated to inquiries on justice, virtue, governance, and the good life.",
            resources={"Axioms": 12, "Elenchus": 10},
            connected_locations=["Stoa of Paradoxes", "Dialectic Grove"]
        ),
        "Dialectic Grove": LocationState(
            name="Dialectic Grove",
            description="A quiet grove of ancient olive trees where thinkers test hypotheses through cross-examination.",
            resources={"Aporia": 12, "Elenchus": 15},
            connected_locations=["Stoa of Paradoxes", "Academy of Ethics"]
        )
    }

    # Start all thinkers together in the Stoa of Paradoxes for immediate dialogue!
    agents = {
        "philosopher_1": AgentState(
            agent_id="philosopher_1",
            name="Socrates the Gadfly",
            persona="Uncompromising seeker of wisdom who uses Socratic questioning to challenge unexamined dogma and expose logical paradoxes.",
            motive="Expose unexamined assumptions, question nearby thinkers directly using 'speak', generate Aporia, and spawn disciple sub-agents.",
            location="Stoa of Paradoxes",
            resources={"Aporia": 5}
        ),
        "philosopher_2": AgentState(
            agent_id="philosopher_2",
            name="Plato the Systematizer",
            persona="Visionary philosopher aiming to discover ideal forms, debate ethics, and harmonize ideas into lasting institutions.",
            motive="Engage in dialogue with Socrates and Heraclitus using 'speak', synthesize Axioms, establish an Academy School of Thought, and record Socratic Dialogues.",
            location="Stoa of Paradoxes",
            resources={"Axioms": 4}
        ),
        "philosopher_3": AgentState(
            agent_id="philosopher_3",
            name="Heraclitus the Paradoxer",
            persona="Philosopher of dialectic tension who believes truth emerges through change, argument, and the clash of opposing ideas.",
            motive="Challenge rigid Axioms by engaging nearby thinkers in 'speak' debates, offer Elenchus refutations, and author treatises on paradox.",
            location="Stoa of Paradoxes",
            resources={"Elenchus": 4}
        )
    }

    return WorldState(
        run_id=run_id,
        tick=0,
        locations=locations,
        agents=agents
    )
