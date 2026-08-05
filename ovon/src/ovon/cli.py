import click
from typing import Optional

from ovon.config import ProjectConfig
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.routing.optimizer import (
    build_greedy_route,
    refine_route_local_search,
    build_random_route,
    build_hotspot_route
)

@click.group()
def cli():
    """Optimal Volunteer Observation Network (OVON) CLI"""
    pass

@cli.command(name="synthetic-generate")
@click.option("--n-sites", default=40, help="Number of candidate observation sites.")
@click.option("--n-species", default=8, help="Number of focal species.")
@click.option("--seed", default=42, help="Random seed.")
def synthetic_generate(n_sites: int, n_species: int, seed: int):
    """Generate a synthetic benchmark dataset."""
    dataset = generate_synthetic_dataset(n_sites=n_sites, n_species=n_species, seed=seed)
    click.echo(f"Generated synthetic landscape with {len(dataset.candidate_sites)} sites.")
    click.echo(f"Focal species count: {dataset.n_species}")
    click.echo(f"Historical observations count: {len(dataset.existing_observations)}")
    click.echo(f"Bootstrap models per species: {dataset.n_bootstrap}")

@cli.command(name="optimize-route")
@click.option("--budget", default=90.0, help="Total route budget in minutes.")
@click.option("--start-site", default=0, help="Start site ID.")
@click.option("--n-sites", default=40, help="Number of candidate sites.")
def optimize_route(budget: float, start_site: int, n_sites: int):
    """Run OVON route optimizer on synthetic dataset."""
    dataset = generate_synthetic_dataset(n_sites=n_sites)
    
    greedy_sol = build_greedy_route(dataset, start_site_id=start_site, budget_minutes=budget)
    refined_sol = refine_route_local_search(greedy_sol, dataset)

    click.echo("=== OVON Route Optimization Result ===")
    click.echo(f"Budget: {budget:.1f} minutes")
    click.echo(f"Initial Greedy Stops: {refined_sol.stop_ids}")
    click.echo(f"Total Stops: {len(refined_sol.sites)}")
    click.echo(f"Travel Time: {refined_sol.total_travel_minutes:.1f} min")
    click.echo(f"Observation Time: {refined_sol.total_observation_minutes:.1f} min")
    click.echo(f"Total Route Time: {refined_sol.total_time_minutes:.1f} min")
    click.echo(f"Multi-Species Utility: {refined_sol.utility:.4f}")

@cli.command(name="evaluate-baseline")
@click.option("--budget", default=90.0, help="Total route budget in minutes.")
@click.option("--seed", default=42, help="Random seed.")
def evaluate_baseline(budget: float, seed: int):
    """Compare OVON optimizer against Random and Hotspot baselines."""
    dataset = generate_synthetic_dataset(n_sites=40, seed=seed)

    rand_sol = build_random_route(dataset, start_site_id=0, budget_minutes=budget, seed=seed)
    hot_sol = build_hotspot_route(dataset, start_site_id=0, budget_minutes=budget)
    
    greedy_sol = build_greedy_route(dataset, start_site_id=0, budget_minutes=budget)
    ovon_sol = refine_route_local_search(greedy_sol, dataset)

    click.echo(f"=== Policy Benchmark Comparison (Budget: {budget:.0f} min) ===")
    click.echo(f"1. Random Policy:    Stops={len(rand_sol.sites)}, Time={rand_sol.total_time_minutes:.1f}m, Utility={rand_sol.utility:.4f}")
    click.echo(f"2. Hotspot Policy:   Stops={len(hot_sol.sites)}, Time={hot_sol.total_time_minutes:.1f}m, Utility={hot_sol.utility:.4f}")
    click.echo(f"3. OVON Policy:      Stops={len(ovon_sol.sites)}, Time={ovon_sol.total_time_minutes:.1f}m, Utility={ovon_sol.utility:.4f}")

if __name__ == "__main__":
    cli()
