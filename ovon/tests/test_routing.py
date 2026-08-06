import pytest

from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.routing.optimizer import (
    build_greedy_route,
    refine_route_local_search,
    build_random_route,
    build_hotspot_route
)

def test_route_budget_constraint():
    dataset = generate_synthetic_dataset(n_sites=30, seed=42)
    budget = 60.0  # minutes

    route = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget)
    assert route.total_time_minutes <= budget + 1e-4

    refined = refine_route_local_search(route, dataset)
    assert refined.total_time_minutes <= budget + 1e-4

def test_route_return_to_hub_budget():
    dataset = generate_synthetic_dataset(n_sites=20, seed=42)
    budget = 75.0
    route = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget, return_to_hub=True)
    
    assert route.total_time_minutes <= budget + 1e-4
    if len(route.stop_ids) > 1:
        # Check return leg travel time is included
        start_id = route.stop_ids[0]
        end_id = route.stop_ids[-1]
        assert dataset.travel_time_matrix[end_id, start_id] > 0.0

def test_excluded_sites_never_selected():
    dataset = generate_synthetic_dataset(n_sites=20, seed=42)
    # Mark site 1 as private and site 2 as unsafe
    dataset.candidate_sites[1].is_public = False
    dataset.candidate_sites[2].is_safe = False

    route = build_greedy_route(dataset, start_site_id=0, budget_minutes=120.0)
    selected_ids = set(route.stop_ids)

    assert 1 not in selected_ids
    assert 2 not in selected_ids

def test_local_search_never_decreases_utility():
    dataset = generate_synthetic_dataset(n_sites=25, seed=123)
    budget = 90.0

    greedy_route = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget)
    refined_route = refine_route_local_search(greedy_route, dataset)

    # Refined route utility should be >= greedy route utility
    assert refined_route.utility >= greedy_route.utility - 1e-5

def test_ovon_policy_outperforms_random():
    dataset = generate_synthetic_dataset(n_sites=35, seed=42)
    budget = 90.0

    rand_route = build_random_route(dataset, start_site_id=0, budget_minutes=budget, seed=42)
    greedy_route = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget)
    ovon_route = refine_route_local_search(greedy_route, dataset)

    assert ovon_route.utility > rand_route.utility

def test_route_cost_breakdown_reconciliation():
    dataset = generate_synthetic_dataset(n_sites=20, seed=42)
    greedy = build_greedy_route(dataset, start_site_id=0, budget_minutes=90.0, return_to_hub=True)
    cbd = greedy.cost_breakdown

    assert cbd is not None
    reconciled_sum = (
        cbd.inter_stop_travel_minutes +
        cbd.return_leg_minutes +
        cbd.stationary_observation_minutes +
        cbd.access_buffer_minutes
    )
    assert abs(reconciled_sum - cbd.total_minutes) < 1e-5
    assert abs(cbd.total_minutes - greedy.total_time_minutes) < 1e-5
