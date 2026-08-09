import random
from typing import List

PHILOSOPHICAL_TOPICS = [
    "Epistemology: How can we distinguish between true knowledge and mere opinion or perception?",
    "Ethics & Justice: Is justice an inherent moral truth, or merely a social contract created by the powerful?",
    "Philosophy of Mind: Can artificial constructs possess genuine consciousness, or do they only simulate thought?",
    "Metaphysics & Time: Does time flow continuously, or is change an illusion of human consciousness?",
    "Political Philosophy: When a law created by an institution conflicts with individual virtue, which must yield?",
    "Aesthetics & Truth: Is beauty a objective form of universal harmony, or a subjective emotional reaction?",
    "Free Will & Causality: If all events are governed by cause and effect, can human choice be truly free?",
    "Language & Meaning: Does language define the limits of what we can conceive, or is thought independent of words?"
]

PROCEDURAL_SHOCKS = [
    "⚡ PROCEDURAL EVENT: A traveler from Alexandria brings a scroll claiming that numbers and geometry are the true essence of reality.",
    "⚡ PROCEDURAL EVENT: A scholar in the Agora presents a paradox: 'This statement is false.' The thinkers are challenged to resolve it.",
    "⚡ PROCEDURAL EVENT: Citizens of the city demand to know whether a ruler should be guided by strict duty or by pragmatic outcome.",
    "⚡ PROCEDURAL EVENT: An ancient inscription found in the Dialectic Grove asserts that memory decays faster than parchment.",
    "⚡ PROCEDURAL EVENT: A young student asks: 'If two noble thinkers arrive at opposite conclusions, how can a seeker find truth?'"
]

def get_random_topic() -> str:
    return random.choice(PHILOSOPHICAL_TOPICS)

def get_random_shock() -> str:
    return random.choice(PROCEDURAL_SHOCKS)
