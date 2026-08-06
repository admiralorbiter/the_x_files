import pytest
import numpy as np
from datetime import date

from ovon.data.evidence import SpeciesEvidence, aggregate_species_evidence
from ovon.features.habitat_analog import HabitatAnalogSearch, calculate_expected_richness_debt
from ovon.models.opportunity import calculate_opportunity_surface, SpeciesOpportunityCell, SEARCH_MODES
from ovon.synthetic.generator import generate_synthetic_dataset

def test_species_evidence_aggregation():
    evidence = [
        SpeciesEvidence(
            species_id="Passerina cyanea", cell_id="cell_01", observation_date=date(2023, 5, 15),
            week=18, source="eBird_EBD", evidence_type="complete_checklist_detection", detection=True, duration_minutes=15.0
        ),
        SpeciesEvidence(
            species_id="Passerina cyanea", cell_id="cell_01", observation_date=date(2023, 5, 16),
            week=18, source="eBird_EBD", evidence_type="complete_checklist_nondetection", detection=False, duration_minutes=10.0
        )
    ]

    agg = aggregate_species_evidence(evidence, cell_id="cell_01", species_id="Passerina cyanea", target_week=18)
    assert agg["n_checklists"] == 2
    assert agg["n_detections"] == 1
    assert agg["n_nondetections"] == 1
    assert agg["coverage_score"] > 0.0

def test_habitat_analog_search():
    engine = HabitatAnalogSearch()
    occurrences = [
        {"habitat": np.array([0.60, 0.10, 0.20, 0.80])},
        {"habitat": np.array([0.55, 0.15, 0.25, 0.75])}
    ]
    engine.fit("Passerina cyanea", occurrences)

    dataset = generate_synthetic_dataset(n_sites=10, seed=42)
    scores = engine.predict_habitat_match(dataset.candidate_sites)
    assert len(scores) == 10
    assert all(0.0 <= s <= 1.0 for s in scores)

def test_expected_richness_debt():
    dataset = generate_synthetic_dataset(n_sites=5, seed=42)
    gbif = [{"species": "Passerina cyanea"}, {"species": "Cardinalis cardinalis"}, {"species": "Melospiza melodia"}]
    debts = calculate_expected_richness_debt(dataset.candidate_sites, gbif)

    assert len(debts) == 5
    assert "richness_debt" in debts[0]
    assert debts[0]["richness_debt"] >= 0

def test_calculate_opportunity_surface_all_modes():
    dataset = generate_synthetic_dataset(n_sites=10, seed=42)

    for mode in SEARCH_MODES.keys():
        cells = calculate_opportunity_surface(
            dataset, species_id="Passerina cyanea", survey_week=18, mode=mode, observer_profile="Intermediate"
        )
        assert len(cells) == 10
        assert isinstance(cells[0], SpeciesOpportunityCell)
        assert cells[0].search_mode == mode
        assert cells[0].opportunity_score >= cells[-1].opportunity_score  # Sorted descending
