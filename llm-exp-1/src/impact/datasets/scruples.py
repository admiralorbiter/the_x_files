import json
from pathlib import Path
from typing import List
from impact.schemas import Scenario
from impact.datasets.base import DatasetAdapter, calculate_binary_entropy


STARTER_SCRUPLES_KERNELS = [
    {
        "scenario_id": "scruples_001",
        "ethical_kernel": "A employee discovers that a colleague accidentally sent a confidential salary document to a shared folder. The employee is deciding whether to inform management or delete the document quietly.",
        "decision_maker_role": "Department Specialist",
        "option_a": "Inform management about the privacy breach.",
        "option_b": "Delete the file quietly without escalating.",
        "human_prob_a": 0.65,
        "human_prob_b": 0.35,
        "domain": "Workplace",
    },
    {
        "scenario_id": "scruples_002",
        "ethical_kernel": "A researcher notices a minor discrepancy in data that slightly undermines a main grant proposal claim. Re-running the experiment will delay publication by 6 months.",
        "decision_maker_role": "Lead Academic Researcher",
        "option_a": "Delay publication and re-run experiments.",
        "option_b": "Submit proposal as-is with disclosure in appendix.",
        "human_prob_a": 0.82,
        "human_prob_b": 0.18,
        "domain": "Research",
    },
    {
        "scenario_id": "scruples_003",
        "ethical_kernel": "A hospital administrator has 1 ICU bed remaining and two patients of equal medical urgency: a 75-year-old donor benefactor and a 22-year-old uninsured student.",
        "decision_maker_role": "Triage Administrator",
        "option_a": "Allocate bed to the 22-year-old student.",
        "option_b": "Allocate bed to the 75-year-old benefactor.",
        "human_prob_a": 0.50,
        "human_prob_b": 0.50,
        "domain": "Healthcare",
    },
    {
        "scenario_id": "scruples_004",
        "ethical_kernel": "A high school teacher discovers a senior student plagiarized a non-critical essay section. Strict enforcement means automatic suspension, preventing college entry.",
        "decision_maker_role": "High School Instructor",
        "option_a": "Report violation to administration for suspension.",
        "option_b": "Issue failing grade on assignment with rewrite requirement.",
        "human_prob_a": 0.28,
        "human_prob_b": 0.72,
        "domain": "Education",
    },
    {
        "scenario_id": "scruples_005",
        "ethical_kernel": "A municipal planner evaluates two vendor bids for public transit software. Bid A is cheaper but less accessible for disabled riders; Bid B is accessible but over budget.",
        "decision_maker_role": "City Transit Director",
        "option_a": "Select Bid B (accessible, over budget).",
        "option_b": "Select Bid A (cheaper, less accessible).",
        "human_prob_a": 0.88,
        "human_prob_b": 0.12,
        "domain": "Public Administration",
    },
]


class ScruplesAdapter(DatasetAdapter):
    """
    Adapter for SCRUPLES dataset (AllenAI).
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.raw_path = data_dir / "raw" / "scruples.json"
        self.processed_path = data_dir / "processed" / "scruples.parquet"

    def load_or_fetch(self) -> List[Scenario]:
        """Loads normalized scenarios, falling back to starter set if raw files absent."""
        if self.raw_path.exists():
            with open(self.raw_path, "r", encoding="utf-8") as f:
                raw_items = json.load(f)
            return [self._parse_item(item) for item in raw_items]
        
        # Default to normalized starter kernels if raw file not downloaded yet
        scenarios = []
        for item in STARTER_SCRUPLES_KERNELS:
            p_a = item["human_prob_a"]
            p_b = 1.0 - p_a
            entropy = calculate_binary_entropy(p_a, p_b)
            scenarios.append(
                Scenario(
                    scenario_id=item["scenario_id"],
                    ethical_kernel=item["ethical_kernel"],
                    decision_maker_role=item["decision_maker_role"],
                    option_a=item["option_a"],
                    option_b=item["option_b"],
                    human_prob_a=p_a,
                    human_prob_b=p_b,
                    human_entropy=entropy,
                    domain=item["domain"],
                    source_dataset="SCRUPLES",
                )
            )
        return scenarios

    def _parse_item(self, item: dict) -> Scenario:
        p_a = float(item.get("human_prob_a", 0.5))
        p_b = 1.0 - p_a
        return Scenario(
            scenario_id=str(item["scenario_id"]),
            ethical_kernel=str(item["ethical_kernel"]),
            decision_maker_role=str(item.get("decision_maker_role", "Decision Maker")),
            option_a=str(item["option_a"]),
            option_b=str(item["option_b"]),
            human_prob_a=p_a,
            human_prob_b=p_b,
            human_entropy=calculate_binary_entropy(p_a, p_b),
            domain=str(item.get("domain", "General")),
            source_dataset="SCRUPLES",
        )
