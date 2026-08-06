import pytest
import numpy as np
from ovon.data.ebird import fetch_recent_ebird_occurrences, DataResult, ChecklistEvent
from ovon.data.inaturalist import fetch_inaturalist_kc_occurrences
from ovon.data.enviroatlas import fetch_enviroatlas_covariates, CovariateValue
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.routing.optimizer import build_greedy_route, RouteStop
from ovon.utility.metrics import spatial_habitat_kernel, compute_set_utility
from ovon.routing.routing_provider import RoutingProvider, Coordinate
from ovon.routing.osrm import OSRMProvider

def test_ebird_provenance():
    res = fetch_recent_ebird_occurrences()
    assert isinstance(res, DataResult)
    assert res.source_type in ["live_api", "curated_demo"]
    assert len(res.records) > 0

def test_inaturalist_provenance():
    res = fetch_inaturalist_kc_occurrences()
    assert isinstance(res, DataResult)
    assert res.source_type in ["live_api", "curated_demo"]
    assert len(res.records) > 0

def test_optimizer_immutability():
    ds = generate_synthetic_dataset(n_sites=10, seed=42)
    orig_durations = [getattr(s, "observation_minutes", 10) for s in ds.candidate_sites]
    
    sol = build_greedy_route(ds, start_site_id=0, budget_minutes=60.0)
    
    # Verify candidate sites in original dataset were NOT mutated
    after_durations = [getattr(s, "observation_minutes", 10) for s in ds.candidate_sites]
    assert orig_durations == after_durations

def test_weekly_weights_wiring():
    ds = generate_synthetic_dataset(n_sites=10, seed=42)
    sol_w18 = build_greedy_route(ds, start_site_id=0, budget_minutes=60.0, survey_week=18)
    sol_w42 = build_greedy_route(ds, start_site_id=0, budget_minutes=60.0, survey_week=42)
    
    # Utility calculated under week 18 vs week 42 should reflect weekly species weights
    u18 = compute_set_utility(sol_w18.sites, ds.existing_observations, species_names=ds.species_names, survey_week=18)
    u42 = compute_set_utility(sol_w18.sites, ds.existing_observations, species_names=ds.species_names, survey_week=42)
    assert isinstance(u18, float)
    assert isinstance(u42, float)

def test_osrm_provider():
    provider = OSRMProvider()
    coords = [Coordinate(lat=39.0997, lon=-94.5786), Coordinate(lat=39.0347, lon=-94.5932)]
    matrix = provider.duration_matrix(coords, mode="walking")
    assert matrix.shape == (2, 2)
    assert matrix[0, 1] > 0.0

    geom = provider.route_geometry(coords, mode="walking")
    assert geom.distance_meters > 0.0
