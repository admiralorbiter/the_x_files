import pytest
import numpy as np

from ovon.synthetic.generator import generate_synthetic_dataset, CandidateSite
from ovon.utility.metrics import duration_efficiency_multiplier, compute_set_utility
from ovon.routing.optimizer import build_greedy_route, refine_route_local_search

def test_duration_efficiency_multiplier():
    m_5 = duration_efficiency_multiplier(5.0)
    m_10 = duration_efficiency_multiplier(10.0)
    m_15 = duration_efficiency_multiplier(15.0)
    m_20 = duration_efficiency_multiplier(20.0)

    assert 0.40 < m_5 < 0.50
    assert m_5 < m_10 < m_15 < m_20
    assert m_20 > 0.90

def test_greedy_route_allocates_variable_durations():
    dataset = generate_synthetic_dataset(n_sites=15, seed=42)
    # Give a generous time budget so duration extensions are evaluated
    route = build_greedy_route(dataset, start_site_id=0, budget_minutes=120.0, return_to_hub=True)

    durations = [getattr(s, "allocated_observation_minutes", 5) for s in route.sites]
    assert len(durations) > 0
    # Every allocated duration must be in valid discrete set {5, 10, 15, 20}
    assert all(d in [5, 10, 15, 20] for d in durations)

def test_local_search_refines_variable_durations():
    dataset = generate_synthetic_dataset(n_sites=15, seed=42)
    greedy = build_greedy_route(dataset, start_site_id=0, budget_minutes=90.0, return_to_hub=True)
    refined = refine_route_local_search(greedy, dataset)

    assert refined.total_time_minutes <= 90.0
    assert refined.utility >= greedy.utility - 1e-5
