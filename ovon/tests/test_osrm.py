import pytest
from ovon.routing.osrm import (
    haversine_distance_km,
    fallback_geodesic_route,
    fetch_osrm_route,
    fetch_osrm_multistop_route
)

def test_haversine_distance():
    # Distance between KC Downtown (39.0997, -94.5786) and Swope Park (38.9953, -94.5262) ~ 12.3 km
    dist = haversine_distance_km(39.0997, -94.5786, 38.9953, -94.5262)
    assert 10.0 <= dist <= 15.0

def test_fallback_geodesic_route():
    res = fallback_geodesic_route(39.0997, -94.5786, 38.9953, -94.5262)
    assert res["duration_min"] > 0.0
    assert res["distance_km"] > 0.0
    assert len(res["polyline_coords"]) == 10
    assert res["is_fallback"] is True

def test_fetch_osrm_route_structure():
    res = fetch_osrm_route(39.0997, -94.5786, 38.9953, -94.5262)
    assert "duration_min" in res
    assert "distance_km" in res
    assert "polyline_coords" in res
    assert "steps" in res
    assert len(res["polyline_coords"]) > 0

def test_fetch_osrm_multistop_route():
    coords = [(39.0997, -94.5786), (38.9953, -94.5262), (38.9867, -94.3161)]
    res = fetch_osrm_multistop_route(coords)
    assert res["duration_min"] > 0.0
    assert res["distance_km"] > 0.0
    assert len(res["polyline_coords"]) >= 3
