from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
import numpy as np

from ovon.synthetic.generator import CandidateSite, SyntheticDataset
from ovon.utility.metrics import compute_set_utility, calculate_qbc_disagreement

@dataclass
class RouteCostBreakdown:
    inter_stop_travel_minutes: float
    return_leg_minutes: float
    stationary_observation_minutes: float
    access_buffer_minutes: float
    total_minutes: float

@dataclass
class RouteSolution:
    sites: List[CandidateSite]
    stop_ids: List[int]
    total_travel_minutes: float
    total_observation_minutes: float
    total_time_minutes: float
    utility: float
    budget_minutes: float
    cost_breakdown: Optional[RouteCostBreakdown] = None

def calculate_route_travel_time(
    stop_ids: List[int],
    travel_matrix: np.ndarray,
    return_to_hub: bool = True
) -> float:
    """Calculate total travel time for a sequence of stops, including optional return-to-hub leg."""
    if len(stop_ids) <= 1:
        return 0.0
    travel = 0.0
    for i in range(len(stop_ids) - 1):
        travel += travel_matrix[stop_ids[i], stop_ids[i+1]]
    if return_to_hub and len(stop_ids) > 1:
        travel += travel_matrix[stop_ids[-1], stop_ids[0]]
    return float(travel)

def calculate_route_cost_breakdown(
    stops: List[CandidateSite],
    stop_ids: List[int],
    travel_matrix: np.ndarray,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteCostBreakdown:
    """Calculate explicit cost breakdown across inter-stop travel, return leg, stationary obs, and access buffers."""
    inter_travel = 0.0
    for i in range(len(stop_ids) - 1):
        inter_travel += float(travel_matrix[stop_ids[i], stop_ids[i+1]])
    
    return_leg = 0.0
    if return_to_hub and len(stop_ids) > 1:
        return_leg = float(travel_matrix[stop_ids[-1], stop_ids[0]])

    stat_obs = sum(float(s.observation_minutes) for s in stops)
    access_buf = sum(float(access_buffer_minutes) for s in stops)

    total_m = inter_travel + return_leg + stat_obs + access_buf
    return RouteCostBreakdown(
        inter_stop_travel_minutes=inter_travel,
        return_leg_minutes=return_leg,
        stationary_observation_minutes=stat_obs,
        access_buffer_minutes=access_buf,
        total_minutes=total_m
    )

def calculate_route_total_time(
    stops: List[CandidateSite],
    stop_ids: List[int],
    travel_matrix: np.ndarray,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> Tuple[float, float, float]:
    """Calculate (travel_minutes, obs_minutes, total_minutes) with parking/access buffers."""
    cbd = calculate_route_cost_breakdown(stops, stop_ids, travel_matrix, return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes)
    return cbd.inter_stop_travel_minutes + cbd.return_leg_minutes, cbd.stationary_observation_minutes + cbd.access_buffer_minutes, cbd.total_minutes

def filter_valid_candidates(dataset: SyntheticDataset) -> List[CandidateSite]:
    """Filter out non-public or unsafe candidate sites."""
    return [s for s in dataset.candidate_sites if s.is_public and s.is_safe]

def build_greedy_route(
    dataset: SyntheticDataset,
    start_site_id: int,
    budget_minutes: float,
    lambda_redundancy: float = 0.5,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteSolution:
    """
    Construct a route greedily based on marginal utility gain per minute added.
    """
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    if start_site_id not in site_dict:
        start_site_id = valid_sites[0].site_id

    current_stops = [site_dict[start_site_id]]
    current_ids = [start_site_id]
    visited_ids: Set[int] = {start_site_id}

    current_utility = compute_set_utility(
        current_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy
    )

    while True:
        best_candidate: Optional[CandidateSite] = None
        best_efficiency = -1e9
        best_added_time = 0.0
        best_new_utility = current_utility

        for site_id, candidate in site_dict.items():
            if site_id in visited_ids:
                continue

            test_ids = current_ids + [site_id]
            test_stops = current_stops + [candidate]

            travel_m, obs_m, total_m = calculate_route_total_time(
                test_stops, test_ids, dataset.travel_time_matrix,
                return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
            )

            if total_m > budget_minutes:
                continue

            new_utility = compute_set_utility(
                test_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy
            )
            marginal_u = new_utility - current_utility

            # Added time
            cur_travel_m, cur_obs_m, cur_tot_m = calculate_route_total_time(
                current_stops, current_ids, dataset.travel_time_matrix,
                return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
            )
            added_time = total_m - cur_tot_m
            if added_time <= 0:
                added_time = 0.1

            efficiency = marginal_u / added_time

            if efficiency > best_efficiency and marginal_u > 0:
                best_efficiency = efficiency
                best_candidate = candidate
                best_added_time = added_time
                best_new_utility = new_utility

        if best_candidate is not None:
            current_stops.append(best_candidate)
            current_ids.append(best_candidate.site_id)
            visited_ids.add(best_candidate.site_id)
            current_utility = best_new_utility
        else:
            break

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )

    return RouteSolution(
        sites=current_stops,
        stop_ids=current_ids,
        total_travel_minutes=cbd.inter_stop_travel_minutes + cbd.return_leg_minutes,
        total_observation_minutes=cbd.stationary_observation_minutes + cbd.access_buffer_minutes,
        total_time_minutes=cbd.total_minutes,
        utility=current_utility,
        budget_minutes=budget_minutes,
        cost_breakdown=cbd
    )

def refine_route_local_search(
    route: RouteSolution,
    dataset: SyntheticDataset,
    lambda_redundancy: float = 0.5,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteSolution:
    """
    Refine a route using 2-opt reordering and candidate insertion/swap local search.
    """
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    current_ids = list(route.stop_ids)
    current_stops = list(route.sites)
    budget = route.budget_minutes

    improved = True
    while improved:
        improved = False

        # 1. 2-opt reordering (keep start fixed)
        n_stops = len(current_ids)
        if n_stops >= 3:
            for i in range(1, n_stops - 1):
                for j in range(i + 1, n_stops):
                    new_ids = current_ids[:i] + current_ids[i:j+1][::-1] + current_ids[j+1:]
                    new_stops = [site_dict[sid] for sid in new_ids]
                    
                    t_m, o_m, tot_m = calculate_route_total_time(
                        new_stops, new_ids, dataset.travel_time_matrix,
                        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
                    )
                    if tot_m <= budget:
                        new_u = compute_set_utility(new_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy)
                        cur_travel = calculate_route_travel_time(current_ids, dataset.travel_time_matrix, return_to_hub=return_to_hub)
                        if t_m < cur_travel - 1e-4:
                            current_ids = new_ids
                            current_stops = new_stops
                            improved = True
                            break
                if improved:
                    break

        n = len(current_ids)
        if n < 3:
            break

        for i in range(1, n - 1):
            for j in range(i + 1, n):
                test_ids = current_ids[:i] + list(reversed(current_ids[i:j+1])) + current_ids[j+1:]
                test_stops = [site_dict[sid] for sid in test_ids]

                t_m, o_m, tot_m = calculate_route_total_time(
                    test_stops, test_ids, dataset.travel_time_matrix,
                    return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
                )
                
                if tot_m <= budget:
                    cur_u = compute_set_utility(current_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy)
                    new_u = compute_set_utility(test_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy)
                    if new_u > cur_u + 1e-5:
                        current_ids = test_ids
                        current_stops = test_stops
                        improved = True
                        break
            if improved:
                break

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    final_u = compute_set_utility(current_stops, dataset.existing_observations, lambda_redundancy=lambda_redundancy)

    return RouteSolution(
        sites=current_stops,
        stop_ids=current_ids,
        total_travel_minutes=cbd.inter_stop_travel_minutes + cbd.return_leg_minutes,
        total_observation_minutes=cbd.stationary_observation_minutes + cbd.access_buffer_minutes,
        total_time_minutes=cbd.total_minutes,
        utility=final_u,
        budget_minutes=budget,
        cost_breakdown=cbd
    )

# --- Baseline Generators ---

def build_random_route(
    dataset: SyntheticDataset,
    start_site_id: int,
    budget_minutes: float,
    seed: int = 42,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteSolution:
    """Build a random feasible route under budget."""
    rng = np.random.default_rng(seed)
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    if start_site_id not in site_dict:
        start_site_id = valid_sites[0].site_id

    current_stops = [site_dict[start_site_id]]
    current_ids = [start_site_id]
    visited_ids = {start_site_id}

    unvisited = [s.site_id for s in valid_sites if s.site_id != start_site_id]
    rng.shuffle(unvisited)

    for sid in unvisited:
        candidate = site_dict[sid]
        test_ids = current_ids + [sid]
        test_stops = current_stops + [candidate]
        _, _, tot_m = calculate_route_total_time(
            test_stops, test_ids, dataset.travel_time_matrix,
            return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
        )
        if tot_m <= budget_minutes:
            current_ids.append(sid)
            current_stops.append(candidate)
            visited_ids.add(sid)

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    u = compute_set_utility(current_stops, dataset.existing_observations)

    return RouteSolution(
        sites=current_stops,
        stop_ids=current_ids,
        total_travel_minutes=cbd.inter_stop_travel_minutes + cbd.return_leg_minutes,
        total_observation_minutes=cbd.stationary_observation_minutes + cbd.access_buffer_minutes,
        total_time_minutes=cbd.total_minutes,
        utility=u,
        budget_minutes=budget_minutes,
        cost_breakdown=cbd
    )

def build_hotspot_route(
    dataset: SyntheticDataset,
    start_site_id: int,
    budget_minutes: float,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteSolution:
    """Build a route selecting highest average encounter probabilities (hotspots)."""
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    if start_site_id not in site_dict:
        start_site_id = valid_sites[0].site_id

    # Rank sites by mean species encounter probability
    site_richness = {s.site_id: float(np.mean(s.true_p)) for s in valid_sites}
    sorted_sids = sorted(site_richness.keys(), key=lambda k: site_richness[k], reverse=True)

    current_stops = [site_dict[start_site_id]]
    current_ids = [start_site_id]
    visited_ids = {start_site_id}

    for sid in sorted_sids:
        if sid in visited_ids:
            continue
        candidate = site_dict[sid]
        test_ids = current_ids + [sid]
        test_stops = current_stops + [candidate]
        _, _, tot_m = calculate_route_total_time(
            test_stops, test_ids, dataset.travel_time_matrix,
            return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
        )
        if tot_m <= budget_minutes:
            current_ids.append(sid)
            current_stops.append(candidate)
            visited_ids.add(sid)

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    u = compute_set_utility(current_stops, dataset.existing_observations)

    return RouteSolution(
        sites=current_stops,
        stop_ids=current_ids,
        total_travel_minutes=cbd.inter_stop_travel_minutes + cbd.return_leg_minutes,
        total_observation_minutes=cbd.stationary_observation_minutes + cbd.access_buffer_minutes,
        total_time_minutes=cbd.total_minutes,
        utility=u,
        budget_minutes=budget_minutes,
        cost_breakdown=cbd
    )
