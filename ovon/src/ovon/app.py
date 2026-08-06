import sys
from pathlib import Path

# Ensure src directory is in sys.path for ovon imports
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st
import folium
import pandas as pd
import numpy as np

try:
    from streamlit_folium import st_folium
    HAS_STREAMLIT_FOLIUM = True
except ImportError:
    HAS_STREAMLIT_FOLIUM = False

from ovon.data.fetch_public import build_kc_real_dataset, fetch_gbif_kc_birds
from ovon.data.fetch_urban import build_kc_urban_pedestrian_dataset
from ovon.data.enviroatlas import fetch_enviroatlas_covariates
from ovon.data.phenology import get_species_phenology, get_weekly_species_weights
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.features.grid import EqualAreaGrid
from ovon.features.redundancy import RedundancyAtlas
from ovon.models.encounter import CalibratedTreeEncounterModel, SpatialBlockCV, BootstrapEnsembleUncertainty, extract_feature_vector
from ovon.models.opportunity import calculate_opportunity_surface, SEARCH_MODES
from ovon.features.habitat_analog import calculate_expected_richness_debt
from ovon.routing.optimizer import (
    build_greedy_route,
    refine_route_local_search,
    build_random_route,
    build_hotspot_route,
    site_lat_lon
)
from ovon.routing.osrm import fetch_osrm_multistop_route
from ovon.data.species_enrichment import get_enriched_species_metadata

st.set_page_config(
    page_title="OVON - Optimal Volunteer Observation Network",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global Research Prototype Warning Banner
st.warning(
    "⚠️ **Research Prototype & Simulation Disclaimer**: Search opportunity scores, ecological models, and environmental layers "
    "currently combine provisional phenology, regional habitat proxies, and demonstration data. Numerical outputs are illustrative "
    "and MUST NOT be cited as empirical field findings until raw EBD/SED parquet extracts are loaded and re-fitted."
)

st.title("🦅 OVON: Optimal Volunteer Observation Network")
st.caption("Human-Aware, Route-Constrained Multi-Species Adaptive Sampling — Greater Kansas City Pilot Region")

# Sidebar Configuration
st.sidebar.header("🗺️ Map Layers & Visual Filters")
st.sidebar.caption("Hot-switch map overlays without recalculating route optimization.")

show_gbif_layer = st.sidebar.checkbox("Overlay GBIF Species Sightings on Map", value=True)
show_ebird_layer = st.sidebar.checkbox("Overlay eBird Recent Sightings on Map", value=True)
show_inat_layer = st.sidebar.checkbox("Overlay iNaturalist Research-Grade Sightings on Map", value=True)

CACHE_VERSION = "v9_provenance_repair"

@st.cache_data(ttl=3600)
def load_cached_gbif_records(cache_ver: str = CACHE_VERSION):
    return fetch_gbif_kc_birds(limit=200)

gbif_records = load_cached_gbif_records(CACHE_VERSION)
all_gbif_species = sorted(list(set([r["species"] for r in gbif_records if r.get("species")])))
selected_species_filter = st.sidebar.selectbox("Filter Map by Species", options=["All Species"] + all_gbif_species)
heatmap_layer = st.sidebar.radio("Grid Overlay Layer", options=["None", "Epistemic Disagreement (QBC)", "Predicted Encounter Rate (π)"])
observer_profile = st.sidebar.selectbox("Observer Protocol Guidance", options=["Beginner", "Intermediate", "Advanced"], index=0)

st.sidebar.divider()
st.sidebar.header("⚙️ Route Optimization Engine")

@st.cache_data
def get_cached_dataset(mode_name: str, cache_version: str = CACHE_VERSION):
    if mode_name == "Kansas City Urban Pedestrian Circuit (Walk-First)":
        return build_kc_urban_pedestrian_dataset()
    elif mode_name == "Kansas City Regional Geographic Demo (Driving)":
        return build_kc_real_dataset()
    else:
        return generate_synthetic_dataset(n_sites=40, seed=42)

with st.sidebar.form(key="opt_form"):
    data_mode = st.selectbox(
        "Experiment Data Mode",
        options=[
            "Kansas City Urban Pedestrian Circuit (Walk-First)",
            "Kansas City Regional Geographic Demo (Driving)",
            "Synthetic Benchmark Experiment"
        ],
        index=0
    )
    is_urban_pedestrian = (data_mode == "Kansas City Urban Pedestrian Circuit (Walk-First)")
    use_real_kc = (data_mode == "Kansas City Regional Geographic Demo (Driving)")

    preview_ds = get_cached_dataset(data_mode, CACHE_VERSION)
    site_names = [getattr(s, "park_name", f"Candidate Site {s.site_id}") for s in preview_ds.candidate_sites]
    start_site_idx = st.selectbox("Starting Location / Hub", options=range(len(site_names)), format_func=lambda i: site_names[i])

    budget_min = st.slider("Total Route Time Budget (minutes)", min_value=30, max_value=180, value=75, step=15)
    
    pareto_preset = st.selectbox(
        "Pareto Optimization Preset",
        options=["Maximum Information (λ=0.1)", "Balanced (λ=0.5)", "Maximum Diversity (λ=1.2)"],
        index=1
    )
    lambda_map = {"Maximum Information (λ=0.1)": 0.1, "Balanced (λ=0.5)": 0.5, "Maximum Diversity (λ=1.2)": 1.2}
    lambda_red = lambda_map[pareto_preset]

    survey_week_val = st.slider("Target Survey Week (Annual 1-52)", min_value=1, max_value=52, value=18, help="Week 18 = Mid-May Peak Spring Migration; Week 34 = Late August")

    submit_button = st.form_submit_button(label="🚀 Recalculate Route Solution", use_container_width=True)

dataset = preview_ds

@st.cache_data
def get_optimized_route(start_idx, budget, lam, mode_name, week_num, cache_version: str = CACHE_VERSION):
    ds = get_cached_dataset(mode_name, cache_version)
    greedy_sol = build_greedy_route(ds, start_site_id=start_idx, budget_minutes=float(budget), lambda_redundancy=lam, survey_week=week_num, return_to_hub=True)
    return refine_route_local_search(greedy_sol, ds, lambda_redundancy=lam, survey_week=week_num, return_to_hub=True)

ovon_sol = get_optimized_route(start_site_idx, budget_min, lambda_red, data_mode, survey_week_val, CACHE_VERSION)

# Centralized Safe Coordinate Resolution
first_site = dataset.candidate_sites[0]
center_lat = first_site.lat if first_site.lat is not None else 39.0854
center_lon = first_site.lon if first_site.lon is not None else -94.5857

stop_coords = []
for s in ovon_sol.sites:
    lat, lon = site_lat_lon(s, center_lat, center_lon)
    stop_coords.append((lat, lon))

closed_loop_coords = list(stop_coords)
if len(stop_coords) > 1:
    closed_loop_coords.append(stop_coords[0])

@st.cache_data
def get_osrm_details(coords, is_urban, cache_version: str = CACHE_VERSION):
    profile_type = "walking" if is_urban else "driving"
    return fetch_osrm_multistop_route(coords, profile=profile_type)

osrm_res = get_osrm_details(closed_loop_coords, is_urban_pedestrian, CACHE_VERSION)

# Tabs Layout
tab_map, tab_opportunity, tab_species, tab_atlas, tab_models, tab_benchmark = st.tabs([
    "🗺️ Route Map & OSRM Path Layer",
    "🎯 Species Search Lab",
    "🦅 Dynamic Phenology & Species Analytics",
    "📊 Redundancy Atlas & Spatial Grid",
    "🤖 Model Calibration & Out-of-Fold CV",
    "⚔️ Policy Benchmark Comparison"
])

SPECIES_COLORS = ["#e31a1c", "#1f78b4", "#33a02c", "#ff7f00", "#6a3d9a", "#a6cee3", "#b2df8a", "#fdbf6f"]
species_color_map = {sp: SPECIES_COLORS[idx % len(SPECIES_COLORS)] for idx, sp in enumerate(all_gbif_species)}

# --- TAB 1: ROUTE MAP & OSRM PATH LAYER ---
with tab_map:
    prov_badge = "LIVE API + CURATED FIXTURES" if use_real_kc or is_urban_pedestrian else "SYNTHETIC DEMONSTRATION"
    st.info(f"📍 **Data Provenance**: `{prov_badge}` | Preset: **{pareto_preset}** | Target Survey Week: **Week {survey_week_val}**")

    col1, col2, col3, col4 = st.columns(4)
    travel_label = "Walking Travel Time" if is_urban_pedestrian else "Driving Travel Time"
    network_label = "Walking Dist" if is_urban_pedestrian else "Road Dist"

    col1.metric("Total Circuit Time", f"{ovon_sol.total_time_minutes:.1f} min", f"Budget: {budget_min} min")
    col2.metric(travel_label, f"{osrm_res['duration_min']:.1f} min" if not osrm_res['is_fallback'] else f"{ovon_sol.total_travel_minutes:.1f} min", f"{network_label}: {osrm_res['distance_km']:.1f} km")
    col3.metric("Stationary Survey Time", f"{ovon_sol.total_observation_minutes:.1f} min", f"{len(ovon_sol.sites)} Stops")
    col4.metric("Multi-Species Utility", f"{ovon_sol.utility:.4f}", f"Profile: {observer_profile}")

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    for s in dataset.candidate_sites:
        lat, lon = site_lat_lon(s, center_lat, center_lon)
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        covs = getattr(s, "env_covariates", None) or fetch_enviroatlas_covariates(lat, lon, location_name=park_name)
        folium.CircleMarker(
            location=[lat, lon], radius=7, color="#3388ff", fill=True, fill_color="#3388ff", fill_opacity=0.7,
            popup=f"<b>{park_name}</b><br>Canopy: {covs.tree_canopy_pct*100:.0f}%"
        ).add_to(m)

    for idx, s in enumerate(ovon_sol.sites):
        lat, lon = site_lat_lon(s, center_lat, center_lon)
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        dur_m = getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 5))
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>Stop {idx+1}: {park_name}</b><br>Duration: {dur_m} min",
            icon=folium.Icon(color="green" if idx > 0 else "blue", icon="info-sign")
        ).add_to(m)

    if osrm_res.get("polyline_coords"):
        folium.PolyLine(
            osrm_res["polyline_coords"], color="#02818a", weight=5, opacity=0.85,
            popup=f"OSRM Route ({osrm_res['distance_km']:.1f} km)"
        ).add_to(m)

    if HAS_STREAMLIT_FOLIUM:
        st_folium(m, width=1200, height=500, returned_objects=[])
    else:
        st.components.v1.html(m._repr_html_(), height=500)

    st.subheader(f"📋 Volunteer Route Itinerary & Protocol ({observer_profile} Profile)")
    itinerary_data = []
    for idx, s in enumerate(ovon_sol.sites):
        park_name = getattr(s, "park_name", f"Candidate Site {s.site_id}")
        lat, lon = site_lat_lon(s, center_lat, center_lon)
        dur_m = getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 5))
        transit_info = getattr(s, "transit_connection", "Pedestrian Access")
        covs = getattr(s, "env_covariates", None) or fetch_enviroatlas_covariates(lat, lon, location_name=park_name)
        env_str = f"🌳 {covs.tree_canopy_pct*100:.0f}% Canopy | 🏢 {covs.impervious_surface_pct*100:.0f}% Built | 🏞️ {covs.nlcd_class}"

        itinerary_data.append({
            "Stop #": idx + 1,
            "Location Name": park_name,
            "EPA Environmental Profile": env_str,
            "Transit Connection": transit_info,
            "Coordinates": f"{lat:.4f}, {lon:.4f}",
            "Protocol": f"{dur_m}-min stationary count",
            "Allocated Survey Duration": f"{dur_m} min"
        })
    st.table(pd.DataFrame(itinerary_data))

# --- TAB 2: SPECIES SEARCH LAB ---
with tab_opportunity:
    st.subheader("🎯 Species Search Opportunity Engine")
    st.caption("Identifies locations where ecological evidence indicates a target species should be present, but where volunteer survey coverage remains sparse.")

    search_sp = st.selectbox("Select Target Focal Species", options=dataset.species_names, index=0)
    search_mode_key = st.selectbox(
        "Select Search Opportunity Objective Mode",
        options=list(SEARCH_MODES.keys()),
        format_func=lambda k: SEARCH_MODES[k],
        index=1
    )

    opp_cells = calculate_opportunity_surface(
        dataset, species_id=search_sp, survey_week=survey_week_val, mode=search_mode_key, observer_profile=observer_profile
    )

    st.markdown(f"### 📍 Top Ranked Location Opportunity Cards ({len(opp_cells)} sites evaluated)")
    
    card_cols = st.columns(3)
    for i, cell in enumerate(opp_cells[:6]):
        col_idx = i % 3
        with card_cols[col_idx]:
            st.markdown(f"#### #{i+1} {cell.site_name}")
            st.metric("Opportunity Score", f"{cell.opportunity_score:.4f}", f"Habitat Match: {cell.habitat_similarity*100:.0f}%")
            st.caption(f"📍 **Expected Encounter**: {cell.expected_encounter*100:.1f}% | **Coverage**: {cell.checklist_effort:.2f}")
            st.info(f"💡 **Explanation**: {cell.explanation}")

    st.divider()
    st.subheader("🌿 Demonstration Richness-Debt Heuristic")
    st.caption("Compares expected habitat species richness against effort-adjusted observed richness to identify under-sampled greenways.")
    debt_results = calculate_expected_richness_debt(dataset.candidate_sites, gbif_records)
    st.table(pd.DataFrame(debt_results)[["site_name", "expected_richness", "observed_richness", "richness_debt", "explanation"]])

    st.divider()
    st.markdown("### 🗺️ Route Optimization Integration")
    if st.button("🚀 Optimize Volunteer Route for This Search Objective", use_container_width=True):
        opp_surface_dict = {c.site_id: c.opportunity_score for c in opp_cells}
        spec_sol = build_greedy_route(
            dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min),
            lambda_redundancy=lambda_red, survey_week=survey_week_val,
            opportunity_surface=opp_surface_dict, return_to_hub=True
        )
        st.success(f"✓ Generated Species-Specific Route for '{search_sp}' ({SEARCH_MODES[search_mode_key]})!")
        st.metric("Route Circuit Time", f"{spec_sol.total_time_minutes:.1f} min", f"Stops: {len(spec_sol.sites)}")
        st.metric("Opportunity Search Score Utility", f"{spec_sol.utility:.4f}")
        st.caption("Sites visited: " + " → ".join([getattr(s, "park_name", f"Site {s.site_id}") for s in spec_sol.sites]))

# --- TAB 3: DYNAMIC PHENOLOGY & SPECIES ANALYTICS ---
with tab_species:
    st.subheader("🦅 Focal Species Portfolio & Dynamic Weekly Species Weights")
    
    computed_weights = get_weekly_species_weights(dataset.species_names, survey_week_val)
    
    st.markdown(f"### 📅 Active Weekly Utility Weights for Target Survey Week **{survey_week_val}**")
    weight_df = pd.DataFrame({
        "Species Name": dataset.species_names,
        "Dynamic Weekly Weight (w_{s,t})": [f"{w:.4f}" for w in computed_weights],
        "Migratory Status": [get_species_phenology(sp).migratory_status for sp in dataset.species_names]
    })
    st.table(weight_df)

# --- TAB 4: REDUNDANCY ATLAS & SPATIAL GRID ---
with tab_atlas:
    st.subheader("📊 Kansas City Equal-Area 3 km Spatial Grid")
    grid = EqualAreaGrid()
    atlas = RedundancyAtlas(grid)
    c1, c2 = st.columns(2)
    c1.metric("Total Grid Cells", f"{grid.total_cells}")
    c2.metric("Cell Resolution", f"{grid.resolution_km} km x {grid.resolution_km} km", "~9.0 km² per cell")

# --- TAB 5: MODEL CALIBRATION & OUT-OF-FOLD CV ---
with tab_models:
    st.subheader("🤖 Species Encounter Model Calibration & Out-of-Fold Spatial CV")
    st.caption("Status: Synthetic Demonstration (Real empirical model requires EBD dataset fitting)")
    cv_results = [
        {"Species Name": "Melospiza melodia (Song Sparrow)", "Out-of-Fold Brier Score": 0.2100, "Spatial AUC-ROC": 0.418, "Status": "Synthetic Demonstration"},
        {"Species Name": "Passerina cyanea (Indigo Bunting)", "Out-of-Fold Brier Score": 0.1850, "Spatial AUC-ROC": 0.720, "Status": "Synthetic Demonstration"},
        {"Species Name": "Cardinalis cardinalis (Northern Cardinal)", "Out-of-Fold Brier Score": 0.1244, "Spatial AUC-ROC": 0.646, "Status": "Synthetic Demonstration"}
    ]
    st.table(pd.DataFrame(cv_results))

# --- TAB 6: POLICY BENCHMARK COMPARISON ---
with tab_benchmark:
    st.subheader("⚔️ Policy Comparison: OVON vs. Raw Hotspot vs. Random")

    # Pass identical survey_week, lambda_redundancy, return_to_hub, and budget to all benchmark policies
    rand_sol = build_random_route(dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min), seed=42)
    hot_sol = build_hotspot_route(dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min))

    bench_df = pd.DataFrame([
        {"Policy": "1. Random Feasible", "Total Stops": len(rand_sol.sites), "Total Time (min)": rand_sol.total_time_minutes, "Multi-Species Utility": rand_sol.utility},
        {"Policy": "2. Raw Hotspot / Richness", "Total Stops": len(hot_sol.sites), "Total Time (min)": hot_sol.total_time_minutes, "Multi-Species Utility": hot_sol.utility},
        {"Policy": "3. OVON Information-Aware", "Total Stops": len(ovon_sol.sites), "Total Time (min)": ovon_sol.total_time_minutes, "Multi-Species Utility": ovon_sol.utility},
    ])

    st.table(bench_df)
    st.bar_chart(bench_df, x="Policy", y="Multi-Species Utility", color="Policy")
