import os
import sys
import subprocess
import click
import numpy as np

from ovon.config import ProjectConfig
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.data.fetch_public import build_kc_real_dataset, fetch_kc_parks_overpass, fetch_gbif_kc_birds
from ovon.data.ebird import fetch_recent_ebird_occurrences
from ovon.data.inaturalist import fetch_inaturalist_kc_occurrences
from ovon.features.grid import EqualAreaGrid
from ovon.features.redundancy import RedundancyAtlas
from ovon.models.encounter import CalibratedTreeEncounterModel, SpatialBlockCV, BootstrapEnsembleUncertainty, extract_feature_vector
from ovon.models.pipeline import run_historical_replay_experiment
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

@cli.command(name="run-experiment")
@click.option("--train-year", default=2022, help="Prior year for training encounter model.")
@click.option("--replay-year", default=2023, help="Target year for historical replay.")
@click.option("--budget", default=90.0, help="Time budget in minutes.")
@click.option("--week", default=18, help="Target survey week.")
def run_experiment(train_year: int, replay_year: int, budget: float, week: int):
    """Run Sprint 3 Rolling Historical Replay Experiment across 5 sampling policies."""
    click.echo(f"=== OVON Sprint 3: Rolling Historical Replay Experiment ===")
    click.echo(f"Train Period: Year {train_year} | Replay Period: Year {replay_year} | Target Week: Week {week}")
    click.echo(f"Time Budget: {budget:.0f} minutes")
    
    res = run_historical_replay_experiment(
        train_year=train_year, replay_year=replay_year, budget_minutes=budget, survey_week=week
    )

    click.echo(f"\nFocal Species: {res.focal_species[0]}")
    click.echo("\nPolicy Benchmark Comparison Table:")
    click.echo(f"{'Policy Name':<35} | {'Stops':<5} | {'Time (m)':<8} | {'Init Brier':<10} | {'Post Brier':<10} | {'Brier Red.':<10} | {'Gain/Min':<10}")
    click.echo("-" * 105)

    for p in res.policy_results:
        click.echo(f"{p.policy_name:<35} | {p.n_stops:<5} | {p.total_time_minutes:<8.1f} | {p.initial_brier_score:<10.4f} | {p.post_observation_brier_score:<10.4f} | {p.brier_score_reduction:<10.4f} | {p.info_gain_per_minute:<10.5f}")

    click.echo("\n[OK] Historical Replay Benchmark completed successfully!")

@cli.command(name="search-lab")
@click.option("--species", default="Passerina cyanea", help="Target focal species.")
@click.option("--mode", default="expected_undocumented", help="Opportunity search mode.")
@click.option("--week", default=18, help="Target survey week (1-52).")
@click.option("--profile", default="Intermediate", help="Observer skill profile.")
def search_lab(species: str, mode: str, week: int, profile: str):
    """Run Species Search Opportunity Engine and generate ranked location cards."""
    from ovon.models.opportunity import calculate_opportunity_surface, SEARCH_MODES
    from ovon.data.fetch_public import build_kc_real_dataset

    click.echo("=== OVON Species Search Opportunity Engine ===")
    click.echo(f"Target Species: {species}")
    click.echo(f"Search Objective Mode: {SEARCH_MODES.get(mode, mode)}")
    click.echo(f"Survey Week: {week} | Observer Profile: {profile}\n")

    dataset = build_kc_real_dataset()
    opportunity_cells = calculate_opportunity_surface(
        dataset, species_id=species, survey_week=week, mode=mode, observer_profile=profile
    )

    click.echo("Top 5 Ranked Candidate Location Opportunity Cards:")
    for rank, cell in enumerate(opportunity_cells[:5], 1):
        click.echo(f"{rank}. {cell.site_name} (Site #{cell.site_id})")
        click.echo(f"   Opportunity Score: {cell.opportunity_score:.4f} | Habitat Match: {cell.habitat_similarity*100:.0f}%")
        click.echo(f"   Expected Encounter: {cell.expected_encounter*100:.1f}% | Prior Checklist Coverage: {cell.checklist_effort:.2f}")
        click.echo(f"   Explanation: {cell.explanation}\n")

@cli.command(name="fetch-data")
@click.option("--region", default="US-MO-095", help="eBird region code for fetch.")
def fetch_data(region: str):
    """Download public datasets (GBIF, iNaturalist, OSM) and rebuild local cache."""
    click.echo(f"=== OVON Data Rebuild & Fetch Pipeline ({region}) ===")
    
    click.echo("1. Fetching OpenStreetMap Kansas City public parks & landmarks...")
    parks = fetch_kc_parks_overpass()
    click.echo(f"   [OK] Retreived {len(parks)} spatial candidate landmarks.")

    click.echo("2. Fetching GBIF presence-only bird occurrence records...")
    birds = fetch_gbif_kc_birds()
    click.echo(f"   [OK] Retreived {len(birds)} GBIF occurrence records.")

    click.echo("3. Querying eBird recent occurrence endpoint...")
    ebird_res = fetch_recent_ebird_occurrences(region_code=region)
    click.echo(f"   [OK] Source: {ebird_res.source_name} ({ebird_res.source_type})")
    click.echo(f"   [OK] Retreived {len(ebird_res.records)} recent eBird sightings.")

    click.echo("4. Querying iNaturalist research-grade occurrences...")
    inat_res = fetch_inaturalist_kc_occurrences()
    click.echo(f"   [OK] Source: {inat_res.source_name} ({inat_res.source_type})")
    click.echo(f"   [OK] Retreived {len(inat_res.records)} iNaturalist observations.")

    click.echo("\n[OK] Dataset rebuild completed successfully!")

@cli.command(name="model-evaluate")
@click.option("--n-samples", default=100, help="Number of training samples.")
@click.option("--n-bootstrap", default=15, help="Number of bootstrap models.")
def model_evaluate(n_samples: int, n_bootstrap: int):
    """Fit species encounter models and evaluate out-of-fold spatial CV metrics."""
    dataset = build_kc_real_dataset()
    rng = np.random.default_rng(42)

    click.echo(f"=== Milestone 4: Species Encounter Model Evaluation ===")
    click.echo(f"Focal Portfolio Size: {dataset.n_species} species")

    coords = np.zeros((n_samples, 2))
    X = np.zeros((n_samples, 7))

    for i in range(n_samples):
        lat = dataset.candidate_sites[i % len(dataset.candidate_sites)].lat
        lon = dataset.candidate_sites[i % len(dataset.candidate_sites)].lon
        coords[i] = [lat, lon]
        hab = dataset.candidate_sites[i % len(dataset.candidate_sites)].habitat
        week = rng.integers(1, 53)
        X[i] = extract_feature_vector(hab, week)

    sb_cv = SpatialBlockCV()
    splits = sb_cv.split(coords)
    click.echo(f"Spatial Block Cross-Validation Splits: {len(splits)} quadrants")

    for sp_idx, sp_name in enumerate(dataset.species_names):
        true_p = dataset.candidate_sites[0].true_p[sp_idx] if len(dataset.candidate_sites[0].true_p) > sp_idx else 0.4
        y = rng.binomial(1, true_p, size=n_samples)

        briers = []
        aucs = []

        for train_idx, val_idx in splits:
            model = CalibratedTreeEncounterModel(species_name=sp_name)
            model.fit(X[train_idx], y[train_idx])
            metrics = model.evaluate(X[val_idx], y[val_idx])
            briers.append(metrics.brier_score)
            aucs.append(metrics.auc_roc)

        click.echo(f"  - Species: {sp_name:<25} | Out-of-Fold Brier: {np.mean(briers):.4f} | Spatial AUC-ROC: {np.mean(aucs):.3f}")

    click.echo("\nFitting Spatial-Temporal Bootstrap Ensemble...")
    bootstrap_engine = BootstrapEnsembleUncertainty(n_bootstrap=n_bootstrap)
    sp_name = dataset.species_names[0]
    y_sp = rng.binomial(1, 0.4, size=n_samples)
    ensemble = bootstrap_engine.fit_ensemble(sp_name, X, y_sp)
    
    X_candidates = X[:5]
    means, qbc_scores = bootstrap_engine.predict_ensemble(ensemble, X_candidates)
    click.echo(f"Ensemble fitted with {len(ensemble)} bootstrap models for '{sp_name}'.")
    click.echo(f"Sample Candidate Predictions: Mean pi = {np.mean(means):.3f}, QBC Disagreement = {np.mean(qbc_scores):.4f}")

@cli.command(name="dashboard")
@click.option("--port", default=8501, help="Port to run Streamlit dashboard server on.")
def dashboard(port: int):
    """Launch the interactive Streamlit Web Research Dashboard."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    click.echo(f"Launching OVON Interactive Web Research Dashboard on port {port}...")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", str(port)]
    subprocess.run(cmd)

@cli.command(name="fetch-kc")
def fetch_kc():
    """Download and report real Kansas City public parks and GBIF bird records."""
    click.echo("Fetching OpenStreetMap Kansas City public parks...")
    parks = fetch_kc_parks_overpass()
    click.echo(f"Retrieved {len(parks)} real public parks / nature preserves in Greater Kansas City.")
    for p in parks[:5]:
        click.echo(f"  - {p['name']} ({p['type']}) at lat={p['lat']:.4f}, lon={p['lon']:.4f}")

    click.echo("\nFetching GBIF species observations for Kansas City...")
    birds = fetch_gbif_kc_birds()
    click.echo(f"Retrieved {len(birds)} species records in Kansas City bounding box.")
    unique_species = list(set([b['species'] for b in birds if b.get('species')]))
    click.echo(f"Sample Species Portfolio ({len(unique_species)} species): {', '.join(unique_species[:6])}")

from ovon.data.fetch_urban import build_kc_urban_pedestrian_dataset, fetch_kc_urban_pois_overpass

@cli.command(name="fetch-urban")
def fetch_urban():
    """Download and report Kansas City urban pedestrian greenways, transit hubs, and fountains."""
    click.echo("Fetching Kansas City urban pedestrian POIs, transit hubs, and fountains...")
    res = fetch_kc_urban_pois_overpass()
    click.echo(f"Source: {res.source}")
    click.echo(f"Retrieved {len(res.records)} urban pedestrian landmarks.")
    for p in res.records[:5]:
        click.echo(f"  - {p['name']} ({p['type']}) | Transit: {p.get('transit_connection', 'Pedestrian')}")

@cli.command(name="optimize-walk")
@click.option("--budget", default=75.0, help="Total route budget in minutes.")
@click.option("--start-site", default=0, help="Start site ID.")
def optimize_walk(budget: float, start_site: int):
    """Run OVON pedestrian route optimizer on urban Kansas City circuit."""
    dataset = build_kc_urban_pedestrian_dataset()
    click.echo("Loaded Kansas City urban pedestrian greenways, transit hubs, & 4.5 km/h walking matrix.")
    
    greedy_sol = build_greedy_route(dataset, start_site_id=start_site, budget_minutes=budget, return_to_hub=True)
    ovon_sol = refine_route_local_search(greedy_sol, dataset, return_to_hub=True)

    click.echo("\n=== OVON Pedestrian Walking Circuit Optimization Result ===")
    click.echo(f"Budget: {budget:.1f} minutes")
    click.echo(f"Total Walking Stops: {len(ovon_sol.sites)}")
    click.echo(f"Walking Travel Time: {ovon_sol.total_travel_minutes:.1f} min")
    click.echo(f"Stationary Survey Time: {ovon_sol.total_observation_minutes:.1f} min")
    click.echo(f"Total Circuit Time: {ovon_sol.total_time_minutes:.1f} min")
    click.echo(f"Multi-Species Information Utility: {ovon_sol.utility:.4f}")

    click.echo("\nRecommended Urban Walking Itinerary:")
    for idx, site in enumerate(ovon_sol.sites):
        park_name = getattr(site, "park_name", f"Site {site.site_id}")
        lat = getattr(site, "lat", 0.0)
        lon = getattr(site, "lon", 0.0)
        transit = getattr(site, "transit_connection", "Pedestrian Access")
        click.echo(f"  Stop {idx+1}: {park_name} ({transit}) - {site.observation_minutes} min micro-survey")

@cli.command(name="grid-build")
@click.option("--radius", default=50.0, help="Pilot region radius in km.")
@click.option("--res", default=3.0, help="Grid resolution in km.")
def grid_build(radius: float, res: float):
    """Generate and display projected 3 km equal-area spatial grid for Kansas City."""
    grid = EqualAreaGrid(radius_km=radius, resolution_km=res)
    click.echo("=== Kansas City Equal-Area Spatial Grid ===")
    click.echo(f"Center Coordinate: ({grid.center_lat:.4f}, {grid.center_lon:.4f})")
    click.echo(f"Radius: {grid.radius_km:.1f} km")
    click.echo(f"Resolution: {grid.resolution_km:.1f} km (cell area ~{res**2:.1f} km²)")
    click.echo(f"Grid Dimensions: {grid.n_rows} rows x {grid.n_cols} cols")
    click.echo(f"Total Spatial Grid Cells: {grid.total_cells}")
    click.echo(f"Bounding Box: Lat [{grid.min_lat:.4f}, {grid.max_lat:.4f}], Lon [{grid.min_lon:.4f}, {grid.max_lon:.4f}]")

@cli.command(name="report-redundancy")
@click.option("--week", default=18, help="Target week (e.g. spring migration week 18).")
@click.option("--top-k", default=5, help="Number of under-sampled cells to report.")
def report_redundancy(week: int, top_k: int):
    """Generate spatiotemporal redundancy atlas and rank under-sampled grid cells."""
    grid = EqualAreaGrid()
    atlas = RedundancyAtlas(grid)

    dataset = build_kc_real_dataset()
    obs_list = []
    for obs in dataset.existing_observations:
        if isinstance(obs, (tuple, list)):
            obs_list.append({
                "lat": grid.center_lat + (obs[1] / 111.0),
                "lon": grid.center_lon + (obs[0] / (111.0 * 0.77)),
                "week": obs[3],
                "observer_id": "obs_sample",
                "habitat": obs[2]
            })
        else:
            obs_lat = getattr(obs, "lat", None)
            if obs_lat is None:
                obs_lat = grid.center_lat + (getattr(obs, "y_km", getattr(obs, "y", 0.0)) / 111.0)
            obs_lon = getattr(obs, "lon", None)
            if obs_lon is None:
                obs_lon = grid.center_lon + (getattr(obs, "x_km", getattr(obs, "x", 0.0)) / (111.0 * 0.77))
            obs_list.append({
                "lat": obs_lat,
                "lon": obs_lon,
                "week": getattr(obs, "week", 18),
                "observer_id": getattr(obs, "observer_id", "obs_sample") or "obs_sample",
                "habitat": getattr(obs, "habitat", np.array([0.33, 0.33, 0.34]))
            })

    atlas.ingest_observations(obs_list)
    top_undersampled = atlas.get_top_undersampled_cells(week=week, top_k=top_k)

    click.echo(f"=== Kansas City Redundancy Atlas (Week {week}) ===")
    click.echo(f"Top {top_k} Priority Under-Observed Spatial Cells:")
    for rank, (cell, metric) in enumerate(top_undersampled, 1):
        click.echo(f"  {rank}. Cell #{cell.cell_id} (Row {cell.row}, Col {cell.col}) - Center: ({cell.center_lat:.4f}, {cell.center_lon:.4f})")
        click.echo(f"     Checklists: {metric.n_checklists}, Coverage Score: {metric.effective_coverage:.4f}, Redundancy Index: {metric.redundancy_index:.4f}")

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
@click.option("--real-kc", is_flag=True, help="Use real Kansas City public park locations.")
def optimize_route(budget: float, start_site: int, n_sites: int, real_kc: bool):
    """Run OVON route optimizer on synthetic or real Kansas City dataset."""
    if real_kc:
        dataset = build_kc_real_dataset()
        click.echo("Loaded real Kansas City public parks & driving travel matrix.")
    else:
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

    if real_kc:
        click.echo("\nRecommended Real Kansas City Route Itinerary:")
        for idx, site in enumerate(refined_sol.sites):
            park_name = getattr(site, "park_name", f"Site {site.site_id}")
            lat = getattr(site, "lat", 0.0)
            lon = getattr(site, "lon", 0.0)
            click.echo(f"  Stop {idx+1}: {park_name} (Lat: {lat:.4f}, Lon: {lon:.4f}) - 10 min stationary survey")

@cli.command(name="evaluate-baseline")
@click.option("--budget", default=90.0, help="Total route budget in minutes.")
@click.option("--real-kc", is_flag=True, help="Use real Kansas City public park locations.")
@click.option("--seed", default=42, help="Random seed.")
def evaluate_baseline(budget: float, real_kc: bool, seed: int):
    """Compare OVON optimizer against Random and Hotspot baselines."""
    if real_kc:
        dataset = build_kc_real_dataset(seed=seed)
        click.echo("Loaded real Kansas City public parks & driving travel matrix.")
    else:
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
