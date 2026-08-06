import pytest
import numpy as np
from datetime import date

from ovon.features.schema import EnvironmentalFeatureVector
from ovon.features.habitat_analog import HabitatAnalogSearch
from ovon.data.evidence import SpeciesEvidence, aggregate_species_evidence, build_species_evidence
from ovon.models.opportunity import calculate_opportunity_surface, get_site_cell_id
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.routing.optimizer import build_random_route, build_hotspot_route, SiteRewardProtocol
from ovon.data.fetch_public import build_kc_real_dataset
from ovon.data.fetch_urban import build_kc_urban_pedestrian_dataset

def test_environmental_feature_vector_immutability():
    """Verify EnvironmentalFeatureVector makes a defensive copy and makes values read-only."""
    orig_vals = np.array([0.4, 0.3, 0.5, 0.6])
    vec = EnvironmentalFeatureVector(
        feature_names=("f1", "f2", "f3", "f4"),
        values=orig_vals
    )
    with pytest.raises(ValueError):
        vec.values[0] = 0.99
    assert vec.values[0] == 0.4

def test_habitat_analog_schema_enforcement():
    """Verify HabitatAnalogSearch raises ValueError on dimension mismatch instead of padding/truncating."""
    engine = HabitatAnalogSearch()
    ds = generate_synthetic_dataset(n_sites=5, seed=42)

    # Fit with background candidate matching schema
    engine.fit("Cardinalis cardinalis", occurrence_records=[{"habitat": ds.candidate_sites[0].habitat}], background_candidates=ds.candidate_sites)

    # Candidate site with mismatched 2-dim habitat should raise ValueError
    class InvalidSite:
        habitat = np.array([0.1, 0.2])

    with pytest.raises(ValueError):
        engine.predict_habitat_match([InvalidSite()])

def test_evidence_deduplication_and_contradictions():
    """Verify aggregate_species_evidence deduplicates detections and identifies contradictions."""
    ev1 = SpeciesEvidence(
        event_id="evt_1", species_id="sp_A", cell_id="cell_0",
        observation_date=date.today(), week=18, source="eBird",
        evidence_type="complete_checklist_detection", detection=True
    )
    ev2 = SpeciesEvidence(
        event_id="evt_1", species_id="sp_A", cell_id="cell_0",
        observation_date=date.today(), week=18, source="eBird",
        evidence_type="complete_checklist_nondetection", detection=False
    )
    ev3 = SpeciesEvidence(
        event_id="evt_2", species_id="sp_A", cell_id="cell_0",
        observation_date=date.today(), week=18, source="eBird",
        evidence_type="complete_checklist_detection", detection=True
    )

    res = aggregate_species_evidence([ev1, ev2, ev3], cell_id="cell_0", species_id="sp_A", target_week=18)
    assert res["n_checklists"] == 2
    assert res["n_detections"] == 2
    assert res["has_contradictions"] is True

def test_build_species_evidence_adapter():
    """Verify build_species_evidence constructs valid SpeciesEvidence from multi-source records."""
    gbif = [{"species": "Cardinalis cardinalis", "lat": 39.1, "lon": -94.5, "week": 18}]
    ebird = [{"species": "Cardinalis cardinalis", "lat": 39.2, "lon": -94.6, "week": 18, "detection": True, "event_id": "e1"}]
    inat = [{"species": "Cardinalis cardinalis", "lat": 39.3, "lon": -94.7, "week": 18, "event_id": "i1"}]

    records = build_species_evidence(gbif_occurrences=gbif, ebird_detections=ebird, inat_occurrences=inat)
    assert len(records) == 3
    sources = {r.source for r in records}
    assert sources == {"GBIF", "eBird", "iNaturalist"}

def test_opportunity_surface_with_species_evidence():
    """Verify calculate_opportunity_surface integrates real SpeciesEvidence."""
    ds = generate_synthetic_dataset(n_sites=10, seed=42)
    s0 = ds.candidate_sites[0]
    lat, lon = (s0.lat if s0.lat is not None else 39.0854), (s0.lon if s0.lon is not None else -94.5857)
    gbif = [{"species": ds.species_names[0], "lat": lat, "lon": lon, "week": 18}]
    ev = build_species_evidence(gbif_occurrences=gbif)

    cells = calculate_opportunity_surface(ds, species_id=ds.species_names[0], survey_week=18, species_evidence=ev)
    assert len(cells) == len(ds.candidate_sites)
    assert not cells[0].is_simulation_only

def test_opportunity_ranking_candidate_order_invariance():
    """Verify ranking is invariant to dataset candidate site list ordering."""
    ds = generate_synthetic_dataset(n_sites=10, seed=42)
    s0 = ds.candidate_sites[0]
    lat, lon = (s0.lat if s0.lat is not None else 39.0854), (s0.lon if s0.lon is not None else -94.5857)
    ev = build_species_evidence(gbif_occurrences=[{"species": ds.species_names[0], "lat": lat, "lon": lon, "week": 18}])

    cells_orig = calculate_opportunity_surface(ds, species_id=ds.species_names[0], survey_week=18, species_evidence=ev)

    ds_rev = generate_synthetic_dataset(n_sites=10, seed=42)
    ds_rev.candidate_sites = list(reversed(ds_rev.candidate_sites))

    cells_rev = calculate_opportunity_surface(ds_rev, species_id=ds_rev.species_names[0], survey_week=18, species_evidence=ev)

    orig_scores = {c.site_id: c.opportunity_score for c in cells_orig}
    rev_scores = {c.site_id: c.opportunity_score for c in cells_rev}

    for sid in orig_scores:
        assert pytest.approx(orig_scores[sid], abs=1e-5) == rev_scores[sid]

def test_baseline_route_builders_accept_parameters():
    """Verify build_random_route and build_hotspot_route accept lambda_redundancy and survey_week."""
    ds = generate_synthetic_dataset(n_sites=10, seed=42)
    rand_sol = build_random_route(ds, start_site_id=0, budget_minutes=60, lambda_redundancy=0.8, survey_week=20)
    hot_sol = build_hotspot_route(ds, start_site_id=0, budget_minutes=60, lambda_redundancy=0.8, survey_week=20)

    assert rand_sol.utility is not None
    assert hot_sol.utility is not None

def test_application_smoke_all_modes():
    """Smoke test executing dataset generation across all three data modes."""
    ds_urban = build_kc_urban_pedestrian_dataset()
    ds_real = build_kc_real_dataset()
    ds_synth = generate_synthetic_dataset(n_sites=15, seed=42)

    for ds in [ds_urban, ds_real, ds_synth]:
        cells = calculate_opportunity_surface(ds, species_id=ds.species_names[0], survey_week=18)
        assert len(cells) == len(ds.candidate_sites)
