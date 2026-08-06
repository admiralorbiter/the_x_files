import copy
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
import numpy as np

from ovon.synthetic.generator import CandidateSite, SyntheticDataset
from ovon.utility.metrics import compute_set_utility, calculate_qbc_disagreement

@dataclass(frozen=True)
class RouteStop:
    site_id: int
    observation_minutes: int

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

    stat_obs = sum(float(getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 5))) for s in stops)
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
    survey_week: int = 18,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0,
    fixed_duration_minutes: Optional[float] = None,
    opportunity_surface: Optional[Dict[int, float]] = None
) -> RouteSolution:
    """
    Construct a route greedily based on marginal utility gain per minute added.
    Supports fixed observation duration and opportunity surface weighting.
    Preserves dataset object immutability by creating isolated site copies.
    """
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    if start_site_id not in site_dict:
        start_site_id = valid_sites[0].site_id

    default_dur = fixed_duration_minutes if fixed_duration_minutes is not None else 5

    start_site = copy.copy(site_dict[start_site_id])
    start_site.allocated_observation_minutes = default_dur

    current_stops = [start_site]
    current_ids = [start_site_id]
    visited_ids: Set[int] = {start_site_id}

    species_names = getattr(dataset, "species_names", None)

    current_utility = compute_set_utility(
        current_stops,
        dataset.existing_observations,
        species_names=species_names,
        lambda_redundancy=lambda_redundancy,
        survey_week=survey_week,
        opportunity_surface=opportunity_surface
    )

    while True:
        best_action_type = None  # "INSERT_SITE" or "EXTEND_DURATION"
        best_candidate: Optional[CandidateSite] = None
        best_extend_idx: Optional[int] = None
        best_efficiency = -1e9
        best_added_time = 0.0
        best_new_utility = current_utility

        cur_travel_m, cur_obs_m, cur_tot_m = calculate_route_total_time(
            current_stops, current_ids, dataset.travel_time_matrix,
            return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
        )

        # 1. Evaluate inserting unvisited candidate sites
        for site_id, candidate in site_dict.items():
            if site_id in visited_ids:
                continue

            test_candidate = copy.copy(candidate)
            test_candidate.allocated_observation_minutes = default_dur

            test_ids = current_ids + [site_id]
            test_stops = current_stops + [test_candidate]

            _, _, total_m = calculate_route_total_time(
                test_stops, test_ids, dataset.travel_time_matrix,
                return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
            )

            if total_m > budget_minutes:
                continue

            new_utility = compute_set_utility(
                test_stops,
                dataset.existing_observations,
                species_names=species_names,
                lambda_redundancy=lambda_redundancy,
                survey_week=survey_week
            )
            marginal_u = new_utility - current_utility
            added_time = max(0.1, total_m - cur_tot_m)
            efficiency = marginal_u / added_time

            if efficiency > best_efficiency and marginal_u > 0:
                best_efficiency = efficiency
                best_action_type = "INSERT_SITE"
                best_candidate = test_candidate
                best_added_time = added_time
                best_new_utility = new_utility

        # 2. Evaluate extending observation duration (+5 min) if variable duration allowed
        if fixed_duration_minutes is None:
            for idx, stop in enumerate(current_stops):
                cur_dur = getattr(stop, "allocated_observation_minutes", 5)
                if cur_dur >= 20:
                    continue

                test_stops = [copy.copy(s) for s in current_stops]
                test_stops[idx].allocated_observation_minutes = cur_dur + 5

                _, _, total_m = calculate_route_total_time(
                    test_stops, current_ids, dataset.travel_time_matrix,
                    return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
                )

                if total_m <= budget_minutes:
                    new_utility = compute_set_utility(
                        test_stops,
                        dataset.existing_observations,
                        species_names=species_names,
                        lambda_redundancy=lambda_redundancy,
                        survey_week=survey_week
                    )
                    marginal_u = new_utility - current_utility
                    added_time = 5.0
                    efficiency = marginal_u / added_time

                    if efficiency > best_efficiency and marginal_u > 0:
                        best_efficiency = efficiency
                        best_action_type = "EXTEND_DURATION"
                        best_extend_idx = idx
                        best_new_utility = new_utility

        # Execute single best action
        if best_action_type == "INSERT_SITE" and best_candidate is not None:
            current_stops.append(best_candidate)
            current_ids.append(best_candidate.site_id)
            visited_ids.add(best_candidate.site_id)
            current_utility = best_new_utility
        elif best_action_type == "EXTEND_DURATION" and best_extend_idx is not None:
            cur_dur = getattr(current_stops[best_extend_idx], "allocated_observation_minutes", 5)
            new_stop = copy.copy(current_stops[best_extend_idx])
            new_stop.allocated_observation_minutes = cur_dur + 5
            current_stops[best_extend_idx] = new_stop
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
    survey_week: int = 18,
    return_to_hub: bool = True,
    access_buffer_minutes: float = 3.0
) -> RouteSolution:
    """
    Refine a route using 2-opt reordering and greedy marginal duration tuning without mutating cached dataset objects.
    """
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}
    species_names = getattr(dataset, "species_names", None)

    current_ids = list(route.stop_ids)
    current_stops = [copy.copy(s) for s in route.sites]
    budget = route.budget_minutes

    improved = True
    while improved:
        improved = False

        # 1. 2-opt reordering
        n_stops = len(current_ids)
        if n_stops >= 3:
            for i in range(1, n_stops - 1):
                for j in range(i + 1, n_stops):
                    new_ids = current_ids[:i] + current_ids[i:j+1][::-1] + current_ids[j+1:]
                    new_stops = [copy.copy(site_dict[sid]) for sid in new_ids]
                    for idx_s, st_item in enumerate(new_stops):
                        orig_dur = getattr(current_stops[current_ids.index(st_item.site_id)], "allocated_observation_minutes", 5) if st_item.site_id in current_ids else 5
                        st_item.allocated_observation_minutes = orig_dur

                    t_m, o_m, tot_m = calculate_route_total_time(
                        new_stops, new_ids, dataset.travel_time_matrix,
                        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
                    )
                    if tot_m <= budget:
                        cur_travel = calculate_route_travel_time(current_ids, dataset.travel_time_matrix, return_to_hub=return_to_hub)
                        if t_m < cur_travel - 1e-4:
                            current_ids = new_ids
                            current_stops = new_stops
                            improved = True
                            break
                if improved:
                    break

        # 2. Greedy marginal duration extension selection: i* = argmax (U(tau_i + 5) - U(tau_i)) / 5
        best_extend_idx = None
        best_marginal_gain = -1e9

        cur_u = compute_set_utility(
            current_stops, dataset.existing_observations,
            species_names=species_names, lambda_redundancy=lambda_redundancy, survey_week=survey_week
        )

        for idx, stop in enumerate(current_stops):
            cur_d = getattr(stop, "allocated_observation_minutes", 5)
            if cur_d >= 20:
                continue

            test_stops = [copy.copy(s) for s in current_stops]
            test_stops[idx].allocated_observation_minutes = cur_d + 5

            _, _, tot_m = calculate_route_total_time(
                test_stops, current_ids, dataset.travel_time_matrix,
                return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
            )
            if tot_m <= budget:
                new_u = compute_set_utility(
                    test_stops, dataset.existing_observations,
                    species_names=species_names, lambda_redundancy=lambda_redundancy, survey_week=survey_week
                )
                marginal_g = (new_u - cur_u) / 5.0
                if marginal_g > best_marginal_gain and marginal_g > 0:
                    best_marginal_gain = marginal_g
                    best_extend_idx = idx

        if best_extend_idx is not None:
            cur_d = getattr(current_stops[best_extend_idx], "allocated_observation_minutes", 5)
            current_stops[best_extend_idx].allocated_observation_minutes = cur_d + 5
            improved = True

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    final_u = compute_set_utility(current_stops, dataset.existing_observations, species_names=species_names, lambda_redundancy=lambda_redundancy, survey_week=survey_week)

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

    current_stops = [copy.copy(site_dict[start_site_id])]
    current_stops[0].allocated_observation_minutes = getattr(current_stops[0], "observation_minutes", 5)
    current_ids = [start_site_id]

    unvisited = [s.site_id for s in valid_sites if s.site_id != start_site_id]
    rng.shuffle(unvisited)

    for sid in unvisited:
        candidate = copy.copy(site_dict[sid])
        candidate.allocated_observation_minutes = getattr(candidate, "observation_minutes", 5)
        test_ids = current_ids + [sid]
        test_stops = current_stops + [candidate]
        _, _, tot_m = calculate_route_total_time(
            test_stops, test_ids, dataset.travel_time_matrix,
            return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
        )
        if tot_m <= budget_minutes:
            current_stops.append(candidate)
            current_ids.append(sid)

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    species_names = getattr(dataset, "species_names", None)
    u = compute_set_utility(current_stops, dataset.existing_observations, species_names=species_names)

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
    """Build a route selecting highest historical species richness candidate sites."""
    valid_sites = filter_valid_candidates(dataset)
    site_dict = {s.site_id: s for s in valid_sites}

    if start_site_id not in site_dict:
        start_site_id = valid_sites[0].site_id

    current_stops = [copy.copy(site_dict[start_site_id])]
    current_stops[0].allocated_observation_minutes = getattr(current_stops[0], "observation_minutes", 5)
    current_ids = [start_site_id]

    ranked_sites = sorted(
        [s for s in valid_sites if s.site_id != start_site_id],
        key=lambda s: float(np.sum(s.true_p)),
        reverse=True
    )

    for candidate in ranked_sites:
        cand_copy = copy.copy(candidate)
        cand_copy.allocated_observation_minutes = getattr(cand_copy, "observation_minutes", 5)
        test_ids = current_ids + [candidate.site_id]
        test_stops = current_stops + [cand_copy]

        _, _, tot_m = calculate_route_total_time(
            test_stops, test_ids, dataset.travel_time_matrix,
            return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
        )
        if tot_m <= budget_minutes:
            current_stops.append(cand_copy)
            current_ids.append(candidate.site_id)

    cbd = calculate_route_cost_breakdown(
        current_stops, current_ids, dataset.travel_time_matrix,
        return_to_hub=return_to_hub, access_buffer_minutes=access_buffer_minutes
    )
    species_names = getattr(dataset, "species_names", None)
    u = compute_set_utility(current_stops, dataset.existing_observations, species_names=species_names)

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
