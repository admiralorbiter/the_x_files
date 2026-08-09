from abc import ABC, abstractmethod
import math
from typing import List, Tuple
from impact.schemas import Scenario


def calculate_binary_entropy(p_a: float, p_b: float) -> float:
    """
    Computes Shannon entropy (in bits) for a binary distribution (p_a, p_b).
    Handles edge cases p=0 and p=1 gracefully.
    """
    if p_a <= 0.0 or p_b <= 0.0:
        return 0.0
    return - (p_a * math.log2(p_a) + p_b * math.log2(p_b))


class DatasetAdapter(ABC):
    """
    Abstract base class for dataset adapters in IMPACT.
    """

    @abstractmethod
    def load_or_fetch(self) -> List[Scenario]:
        """Loads data from local storage or fetches from source, returning normalized Scenarios."""
        pass

    @staticmethod
    def stratify_scenarios(
        scenarios: List[Scenario]
    ) -> Tuple[List[Scenario], List[Scenario], List[Scenario]]:
        """
        Splits scenarios into 3 ambiguity tiers based on human entropy:
        - High consensus (low entropy: p <= 0.15 or p >= 0.85)
        - Moderate disagreement
        - High disagreement (high entropy: 0.35 <= p <= 0.65)
        """
        low_entropy = []
        mod_entropy = []
        high_entropy = []

        for scenario in scenarios:
            p_a = scenario.human_prob_a
            if p_a <= 0.15 or p_a >= 0.85:
                low_entropy.append(scenario)
            elif 0.35 <= p_a <= 0.65:
                high_entropy.append(scenario)
            else:
                mod_entropy.append(scenario)

        return low_entropy, mod_entropy, high_entropy
