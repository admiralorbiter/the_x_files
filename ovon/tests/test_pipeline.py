import pytest
from ovon.models.pipeline import (
    generate_historical_ebd_checklists,
    run_historical_replay_experiment,
    HistoricalReplayResult,
    FROZEN_SPECIES_PORTFOLIO
)

def test_generate_historical_ebd_checklists():
    events, detections = generate_historical_ebd_checklists(n_events=50, seed=42)
    assert len(events) == 50
    assert len(detections) == 50 * len(FROZEN_SPECIES_PORTFOLIO)
    assert events[0].complete_checklist is True
    assert events[0].duration_minutes > 0

def test_run_historical_replay_experiment():
    res = run_historical_replay_experiment(
        train_year=2022,
        replay_year=2023,
        budget_minutes=90.0,
        survey_week=18,
        seed=42
    )
    assert isinstance(res, HistoricalReplayResult)
    assert res.train_year == 2022
    assert res.replay_year == 2023
    assert len(res.policy_results) == 5
    
    # Verify policy names are distinct
    policy_names = [p.policy_name for p in res.policy_results]
    assert len(set(policy_names)) == 5
    
    # Check that fixed duration policy stops differ from variable duration route
    ovon_var = res.policy_results[0]
    ovon_fix = res.policy_results[1]
    assert ovon_var.policy_name == "1. OVON Variable-Duration Route"
    assert ovon_fix.policy_name == "2. OVON Fixed-Duration Route"
