import pytest
from ovon.data.fetch_public import (
    haversine_distance_km,
    fetch_kc_parks_overpass,
    fetch_gbif_kc_birds,
    build_kc_real_dataset
)

def test_haversine_distance():
    # Distance from KC (39.0997, -94.5786) to St. Louis (38.6270, -90.1994) is ~390 km
    dist = haversine_distance_km(39.0997, -94.5786, 38.6270, -90.1994)
    assert 380.0 <= dist <= 410.0

def test_kc_parks_fallback():
    parks = fetch_kc_parks_overpass()
    assert len(parks) >= 5
    first_park = parks[0]
    assert "name" in first_park
    assert "lat" in first_park
    assert "lon" in first_park
    assert 38.0 <= first_park["lat"] <= 40.0

def test_build_kc_real_dataset():
    dataset = build_kc_real_dataset()
    assert len(dataset.candidate_sites) >= 5
    assert dataset.travel_time_matrix.shape == (len(dataset.candidate_sites), len(dataset.candidate_sites))
    # Check that travel time is non-negative
    assert (dataset.travel_time_matrix >= 0.0).all()
