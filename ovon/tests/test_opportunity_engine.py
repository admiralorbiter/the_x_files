import pytest
import numpy as np
from datetime import date

from ovon.data.evidence import SpeciesEvidence, aggregate_species_evidence
from ovon.features.habitat_analog import HabitatAnalogSearch, calculate_expected_richness_debt
from ovon.features.schema import EnvironmentalFeatureVector
from ovon.models.opportunity import calculate_opportunity_surface, SpeciesOpportunityCell, SEARCH_MODES
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.routing.optimizer import build_greedy_route, site_lat_lon
from ovon.utility.metrics import compute_set_utility, calculate_qbc_disagreement

def test_environmental_feature_vector_schema():
    schema = EnvironmentalFeatureVector(
        feature_names=("canopy", "built", "water"),
        values=np.array([0.40, 0.30, 0.50])
    )
    assert schema.get_value("canopy") == 0.40

    with pytest.raises(ValueError):
        EnvironmentalFeatureVector(
            feature_names=("canopy", "built"),
            values=np.array([0.40, 0.30, 0.50])
        )

def test_species_evidence_event_deduplication_and_cyclic_week():
    # 1 checklist with 8 species should count as 1 checklist (event_id="cl_001")
    evidence = [
        SpeciesEvidence(
            event_id="cl_001", species_id=f"species_{i}", cell_id="cell_01",
            observation_date=date(2023, 1, 2), week=52, source="eBird_EBD",
            evidence_type="complete_checklist_detection", detection=True
        ) for i in range(8)
    ]

    # Target week 1 should recognize week 52 as adjacent (cyclic distance = 1)
    agg = aggregate_species_evidence(evidence, cell_id="cell_01", species_id="species_0", target_week=1)
    assert agg["n_checklists"] == 1
    assert agg["n_detections"] == 1
    assert agg["coverage_score"] > 0.0

def test_opportunity_surface_routing_regression():
    """Verify that reversing opportunity scores in opportunity_surface alters site selection."""
    dataset = generate_synthetic_dataset(n_sites=10, seed=42)

    # Standard greedy route without opportunity surface
    base_sol = build_greedy_route(dataset, start_site_id=0, budget_minutes=60.0)

    # Give site #1 maximum opportunity score (100.0) vs other sites (0.001)
    opp_surface = {s.site_id: 0.001 for s in dataset.candidate_sites}
    opp_surface[1] = 100.0

    opp_sol = build_greedy_route(dataset, start_site_id=0, budget_minutes=60.0, opportunity_surface=opp_surface)

    # Site #1 must be selected in the opportunity-weighted route
    assert 1 in opp_sol.stop_ids
    assert opp_sol.stop_ids != base_sol.stop_ids

def test_qbc_from_bootstrap_matrix_not_true_p():
    """Verify compute_set_utility calculates QBC from bootstrap_predictions when qbc_scores is None."""
    dataset = generate_synthetic_dataset(n_sites=3, seed=42)
    for s in dataset.candidate_sites:
        s.qbc_scores = None
        s.bootstrap_predictions = np.array([[0.1, 0.9], [0.8, 0.2]])  # High disagreement

    u = compute_set_utility(dataset.candidate_sites[:2], dataset.existing_observations)
    assert u > 0.0

def test_synthetic_site_lat_lon_resolution():
    """Verify site_lat_lon handles lat: Optional[float] = None without raising TypeError."""
    dataset = generate_synthetic_dataset(n_sites=3, seed=42)

    for s in dataset.candidate_sites:
        s.lat = None
        s.lon = None
        lat, lon = site_lat_lon(s, center_lat=39.0854, center_lon=-94.5857)
        assert isinstance(lat, float)
        assert isinstance(lon, float)
        assert abs(lat - 39.0854) < 1.0
