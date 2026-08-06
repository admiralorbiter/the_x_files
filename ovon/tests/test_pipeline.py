import pytest
from ovon.models.pipeline import (
    generate_historical_ebd_checklists,
    run_historical_replay_experiment,
    HistoricalReplayResult
)

def test_generate_historical_ebd_checklists():
    events, detections = generate_historical_ebd_checklists(n_events=50, seed=42)
    assert len(events) == 50
    assert len(detections) == 50 * 3
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
    
    ovon_var = res.policy_results[0]
    assert ovon_var.brier_score_reduction > 0.0
    assert ovon_var.info_gain_per_minute > 0.0
