import pytest
import numpy as np

from ovon.data.ebird import (
    fetch_ebird_kc_checklists,
    ebird_checklists_to_existing_observations,
    eBirdChecklistRecord
)

def test_fetch_ebird_kc_checklists():
    records = fetch_ebird_kc_checklists()
    assert len(records) > 0
    first = records[0]
    assert isinstance(first, eBirdChecklistRecord)
    assert first.duration_minutes > 0
    assert first.protocol in ["eBird Stationary", "eBird Traveling", "eBird Complete Checklist"]
    assert len(first.species_list) > 0

def test_ebird_checklists_to_existing_observations():
    records = fetch_ebird_kc_checklists()
    existing_obs = ebird_checklists_to_existing_observations(records)
    assert len(existing_obs) == len(records)
    
    obs1 = existing_obs[0]
    assert hasattr(obs1, "week")
    assert obs1.week > 0
    assert hasattr(obs1, "habitat")
    assert len(obs1.habitat) == 4  # 4D EnviroAtlas feature vector
