import pytest
import numpy as np

from ovon.data.fetch_urban import (
    fetch_kc_urban_pois_overpass,
    build_kc_urban_pedestrian_dataset,
    FALLBACK_KC_URBAN_POIS,
    URBAN_FOCAL_SPECIES
)
from ovon.routing.optimizer import build_greedy_route, refine_route_local_search
from ovon.routing.osrm import fetch_osrm_route, fetch_osrm_multistop_route

def test_fetch_kc_urban_pois():
    res = fetch_kc_urban_pois_overpass()
    assert len(res.records) >= 5
    assert res.source is not None
    # Check transit connection attributes
    assert "transit_connection" in res.records[0]

def test_build_kc_urban_pedestrian_dataset():
    dataset = build_kc_urban_pedestrian_dataset()
    assert len(dataset.candidate_sites) >= 5
    assert dataset.n_species == 8
    
    # Check transit connection field on sites
    site0 = dataset.candidate_sites[0]
    assert hasattr(site0, "transit_connection")
    assert site0.observation_minutes == 5  # 5-min urban micro-count

def test_pedestrian_route_optimizer():
    dataset = build_kc_urban_pedestrian_dataset()
    budget = 60.0  # 60 minute walking budget
    
    greedy = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget, return_to_hub=True)
    ovon_walk = refine_route_local_search(greedy, dataset, return_to_hub=True)
    
    assert ovon_walk.total_time_minutes <= budget + 1e-4
    assert len(ovon_walk.sites) >= 1
    assert ovon_walk.utility > 0.0

def test_osrm_walking_profile():
    # Test walking route structure between Union Station & Penn Valley Park
    start_lat, start_lon = 39.0854, -94.5857
    end_lat, end_lon = 39.0772, -94.5878
    
    res = fetch_osrm_route(start_lat, start_lon, end_lat, end_lon, profile="walking")
    assert "duration_min" in res
    assert "distance_km" in res
    assert "polyline_coords" in res
    assert "steps" in res
    assert res["duration_min"] > 0.0
