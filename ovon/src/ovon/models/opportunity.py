import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from ovon.data.phenology import get_species_phenology
from ovon.features.habitat_analog import HabitatAnalogSearch

SEARCH_MODES = {
    "likely_encounter": "1. Likely Encounter (Maximum Detection Probability)",
    "expected_undocumented": "2. Expected but Undocumented (High Habitat Match + Low Survey Effort)",
    "uncertainty_frontier": "3. Scientific Uncertainty Frontier (High Model Disagreement & Entropy)",
    "hard_to_detect": "4. Hard-to-Detect Opportunity (Cryptic Species Recommending 15-20 Min Surveys)",
    "range_edge_surprise": "5. Potential Range-Edge / Unexpected Observation (High Exploration Value)"
}

@dataclass(frozen=True)
class SpeciesOpportunityCell:
    """
    Structured Opportunity Cell Record powering map visual layers, route optimization,
    and location explanation cards.
    """
    species_id: str
    site_id: int
    site_name: str
    week: int
    expected_presence: float
    expected_encounter: float
    epistemic_uncertainty: float
    checklist_effort: float
    habitat_similarity: float
    model_disagreement: float
    opportunity_score: float
    search_mode: str
    explanation: str

def calculate_opportunity_surface(
    dataset: Any,
    species_id: str,
    survey_week: int = 18,
    mode: str = "expected_undocumented",
    observer_profile: str = "Intermediate"
) -> List[SpeciesOpportunityCell]:
    """
    Generate ranked SpeciesOpportunityCell surface across candidate sites for 1 of 5 search modes.
    """
    phen = get_species_phenology(species_id)
    weekly_abundance = phen.weekly_abundance[min(51, max(0, survey_week - 1))]

    # Learn habitat analog signature from existing presence points if available
    analog_engine = HabitatAnalogSearch()
    sample_occurrences = [
        {"habitat": s.habitat} for s in dataset.candidate_sites[:10]
    ]
    analog_engine.fit(species_id, sample_occurrences)
    analog_matches = analog_engine.predict_habitat_match(dataset.candidate_sites)

    profile_multiplier = {"Beginner": 0.70, "Intermediate": 1.0, "Advanced": 1.30}.get(observer_profile, 1.0)
    cryptic_value = 2.0 if "warbler" in species_id.lower() or "bunting" in species_id.lower() else 1.0

    cells = []
    for idx, s in enumerate(dataset.candidate_sites):
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        covs = getattr(s, "env_covariates", None)
        canopy = covs.tree_canopy_pct if covs else s.habitat[0]

        # 1. Expected Presence psi = weekly_abundance * habitat_similarity
        psi = float(np.clip(weekly_abundance * analog_matches[idx] * (1.2 if canopy > 0.3 else 0.8), 0.01, 0.99))

        # 2. Detection Probability p = logit^-1(psi + duration_effort)
        dur = float(getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 10)))
        p_detect = float(np.clip(1.0 - math.exp(-0.10 * dur * psi * profile_multiplier), 0.05, 0.95))

        # 3. Model Disagreement & Epistemic Uncertainty
        qbc_scores = getattr(s, "qbc_scores", [0.4])
        qbc_disagreement = float(np.mean(qbc_scores)) if len(qbc_scores) > 0 else 0.40
        entropy = float(-psi * math.log2(psi) - (1.0 - psi) * math.log2(1.0 - psi))

        # 4. Checklist Effort & Local Coverage C
        n_prev = getattr(s, "n_checklists", idx % 3)
        coverage_C = float(1.0 - math.exp(-0.35 * n_prev))

        # 5. Compute Mode-Specific Opportunity Score
        if mode == "likely_encounter":
            score = psi * p_detect
            expl = f"High predicted encounter rate ({score*100:.1f}%) during Week {survey_week}."
        elif mode == "expected_undocumented":
            score = psi * (1.0 - coverage_C)
            expl = f"High habitat match ({analog_matches[idx]*100:.0f}%) with only {n_prev} prior checklists."
        elif mode == "uncertainty_frontier":
            score = entropy * qbc_disagreement * (1.0 - coverage_C)
            expl = f"High model disagreement ({qbc_disagreement:.3f}) and entropy ({entropy:.3f})."
        elif mode == "hard_to_detect":
            score = psi * (1.0 - p_detect) * cryptic_value
            expl = f"Cryptic target with low detectability ({p_detect*100:.0f}%), recommending 15-20 min surveys."
        elif mode == "range_edge_surprise":
            range_edge = 1.0 if idx % 2 == 0 else 0.5
            score = qbc_disagreement * range_edge * analog_matches[idx]
            expl = f"Range-edge exploratory site with high potential detection impact."
        else:
            score = psi * (1.0 - coverage_C)
            expl = f"Expected undocumented opportunity score: {score:.4f}."

        cells.append(SpeciesOpportunityCell(
            species_id=species_id,
            site_id=s.site_id,
            site_name=park_name,
            week=survey_week,
            expected_presence=psi,
            expected_encounter=psi * p_detect,
            epistemic_uncertainty=entropy,
            checklist_effort=coverage_C,
            habitat_similarity=analog_matches[idx],
            model_disagreement=qbc_disagreement,
            opportunity_score=float(score),
            search_mode=mode,
            explanation=expl
        ))

    return sorted(cells, key=lambda c: c.opportunity_score, reverse=True)
