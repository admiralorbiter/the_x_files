import pytest
import numpy as np

from ovon.data.inaturalist import fetch_inaturalist_kc_observations, inaturalist_records_to_existing_observations, iNaturalistRecord
from ovon.data.conservation_lands import fetch_conservation_lands, ConservationLandRecord
from ovon.data.wetlands import calculate_wetland_proximity, WetlandProximityProfile

def test_inaturalist_observations():
    recs = fetch_inaturalist_kc_observations()
    assert len(recs) > 0
    first = recs[0]
    assert isinstance(first, iNaturalistRecord)
    assert first.quality_grade == "research"

    obs_list = inaturalist_records_to_existing_observations(recs)
    assert len(obs_list) == len(recs)
    assert hasattr(obs_list[0], "habitat")

def test_conservation_lands():
    lands = fetch_conservation_lands()
    assert len(lands) > 0
    first = lands[0]
    assert isinstance(first, ConservationLandRecord)
    assert "Burr Oak" in first.name or "James A. Reed" in first.name or "Platte Falls" in first.name
    assert first.area_acres > 100.0

def test_wetland_proximity():
    lake_prox = calculate_wetland_proximity(39.0, -94.5, location_name="Loose Park Pond")
    assert lake_prox.distance_to_wetland_km == 0.05
    assert lake_prox.wetland_score > 0.90
