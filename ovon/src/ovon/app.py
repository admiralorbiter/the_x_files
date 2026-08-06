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
from ovon.routing.optimizer import (
    build_greedy_route,
    refine_route_local_search,
    build_random_route,
    build_hotspot_route
)
from ovon.routing.osrm import fetch_osrm_multistop_route
from ovon.data.species_enrichment import get_enriched_species_metadata

st.set_page_config(
    page_title="OVON - Optimal Volunteer Observation Network",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🦅 OVON: Optimal Volunteer Observation Network")
st.caption("Human-Aware, Route-Constrained Multi-Species Adaptive Sampling — Greater Kansas City Pilot Region")

# Sidebar Configuration
st.sidebar.header("🗺️ Map Layers & Visual Filters")
st.sidebar.caption("Hot-switch map overlays without recalculating route optimization.")

show_gbif_layer = st.sidebar.checkbox("Overlay GBIF Species Sightings on Map", value=True)
show_ebird_layer = st.sidebar.checkbox("Overlay eBird Recent Sightings on Map", value=True)
show_inat_layer = st.sidebar.checkbox("Overlay iNaturalist Research-Grade Sightings on Map", value=True)
gbif_records = fetch_gbif_kc_birds(limit=200)
all_gbif_species = sorted(list(set([r["species"] for r in gbif_records if r.get("species")])))
selected_species_filter = st.sidebar.selectbox("Filter Map by Species", options=["All Species"] + all_gbif_species)
heatmap_layer = st.sidebar.radio("Grid Overlay Layer", options=["None", "Epistemic Disagreement (QBC)", "Predicted Encounter Rate (π)"])
observer_profile = st.sidebar.selectbox("Observer Protocol Guidance", options=["Beginner", "Intermediate", "Advanced"], index=0)

st.sidebar.divider()
st.sidebar.header("⚙️ Route Optimization Engine")

CACHE_VERSION = "v7_phenology_graph_restored"

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

stop_coords = []
center_lat = getattr(dataset.candidate_sites[0], "lat", 39.0854)
center_lon = getattr(dataset.candidate_sites[0], "lon", -94.5857)

for s in ovon_sol.sites:
    lat = getattr(s, "lat", center_lat + (s.y / 111.0))
    lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
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
tab_map, tab_species, tab_atlas, tab_models, tab_benchmark = st.tabs([
    "🗺️ Route Map & OSRM Path Layer",
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

    cbd = ovon_sol.cost_breakdown
    if cbd:
        with st.expander("⏱️ Itemized Route Cost Decomposition & Time Reconciliation", expanded=False):
            travel_icon = "🚶" if is_urban_pedestrian else "🚗"
            cost_df = pd.DataFrame([
                {"Component": f"{travel_icon} Inter-Stop Travel Time", "Duration (min)": f"{cbd.inter_stop_travel_minutes:.1f} min", "Notes": "Travel between candidate sites"},
                {"Component": "🔄 Closed-Loop Return Leg to Origin Hub", "Duration (min)": f"{cbd.return_leg_minutes:.1f} min", "Notes": "Circuit leg back to starting hub"},
                {"Component": "🔭 Stationary Observation Time", "Duration (min)": f"{cbd.stationary_observation_minutes:.1f} min", "Notes": f"{len(ovon_sol.sites)} stops @ site survey duration"},
                {"Component": "🎒 Access & Protocol Setup Buffer", "Duration (min)": f"{cbd.access_buffer_minutes:.1f} min", "Notes": f"3.0 min buffer per stop ({len(ovon_sol.sites)} stops)"},
                {"Component": "⏱️ Total Reconciled Circuit Time", "Duration (min)": f"{cbd.total_minutes:.1f} min", "Notes": f"Must stay within {budget_min} min budget"}
            ])
            st.table(cost_df)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    if heatmap_layer != "None":
        st.caption(f"ℹ️ Layer Mode: Displaying `{heatmap_layer}` overlay (Synthetic Demonstration).")
        grid = EqualAreaGrid(radius_km=25.0, resolution_km=8.0)
        for cell in grid.get_all_cells():
            matching_sites = [s for s in dataset.candidate_sites if abs(s.lat - cell.center_lat) < 0.05 and abs(s.lon - cell.center_lon) < 0.05] if hasattr(dataset.candidate_sites[0], "lat") else []
            val = float(np.mean([np.mean(s.true_p) for s in matching_sites])) if matching_sites else 0.3
            color = f"#{int(255*val):02x}{int(255*(1-val)):02x}40" if heatmap_layer == "Epistemic Disagreement (QBC)" else f"#00{int(255*val):02x}{int(255*(1-val)):02x}"
            folium.Rectangle(
                bounds=[[cell.min_lat, cell.min_lon], [cell.max_lat, cell.max_lon]],
                color=color, weight=1, fill=True, fill_color=color, fill_opacity=0.25,
                popup=f"Grid Cell #{cell.cell_id}<br>{heatmap_layer}: {val:.4f}"
            ).add_to(m)

    if show_gbif_layer:
        filtered_gbif = gbif_records
        if selected_species_filter != "All Species":
            filtered_gbif = [r for r in gbif_records if r.get("species") == selected_species_filter]

        for r in filtered_gbif:
            sp_name = r.get("species", "Unknown Bird")
            color = species_color_map.get(sp_name, "#e31a1c")
            folium.CircleMarker(
                location=[r["lat"], r["lon"]], radius=4, color=color, fill=True, fill_color=color, fill_opacity=0.6,
                popup=f"<b>{sp_name}</b><br>Source: GBIF Occurrence"
            ).add_to(m)

    if show_ebird_layer:
        try:
            from ovon.data.ebird import fetch_recent_ebird_occurrences
            ebird_res = fetch_recent_ebird_occurrences()
            for cl in ebird_res.records:
                folium.CircleMarker(
                    location=[cl.lat, cl.lon], radius=6, color="#006d2c", fill=True, fill_color="#2ca25f", fill_opacity=0.9,
                    popup=f"<b>eBird Sighting: {cl.checklist_id}</b><br>{cl.loc_name}<br>Source: {ebird_res.source_type}"
                ).add_to(m)
        except Exception:
            pass

    if show_inat_layer:
        try:
            from ovon.data.inaturalist import fetch_inaturalist_kc_occurrences
            inat_res = fetch_inaturalist_kc_occurrences()
            for r in inat_res.records:
                folium.CircleMarker(
                    location=[r.lat, r.lon], radius=5, color="#54278f", fill=True, fill_color="#756bb1", fill_opacity=0.9,
                    popup=f"<b>iNaturalist #{r.id}</b><br>{r.common_name}<br>Observer: @{r.user_login}"
                ).add_to(m)
        except Exception:
            pass

    for s in dataset.candidate_sites:
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        covs = getattr(s, "env_covariates", None) or fetch_enviroatlas_covariates(lat, lon, location_name=park_name)
        folium.CircleMarker(
            location=[lat, lon], radius=7, color="#3388ff", fill=True, fill_color="#3388ff", fill_opacity=0.7,
            popup=f"<b>{park_name}</b><br>Canopy: {covs.tree_canopy_pct*100:.0f}%"
        ).add_to(m)

    for idx, s in enumerate(ovon_sol.sites):
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
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
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
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

# --- TAB 2: DYNAMIC PHENOLOGY & SPECIES ANALYTICS ---
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

    selected_sp_card = st.selectbox("Select Focal Species to Inspect", options=dataset.species_names, index=0)
    sp_meta = get_enriched_species_metadata(selected_sp_card)

    card_col1, card_col2 = st.columns([1, 2])
    with card_col1:
        st.image(sp_meta.photo_url, caption=f"{sp_meta.common_name} ({sp_meta.scientific_name})", use_container_width=True)
    with card_col2:
        st.markdown(f"### 🦅 {sp_meta.common_name}")
        st.markdown(f"**Scientific Name:** *{sp_meta.scientific_name}*")
        st.markdown(f"**Guild Class:** `{sp_meta.guild_class}`")
        phen = get_species_phenology(sp_meta.common_name)
        st.markdown(f"📅 **Annual Migratory Status:** `{phen.migratory_status}`")
        st.info(f"ℹ️ **Overview:** {sp_meta.description}")

    # Restored 52-Week Phenology Curve Graph
    st.divider()
    st.subheader(f"📈 52-Week Annual Phenology Abundance Curve for {sp_meta.common_name}")
    curr_val = phen.weekly_abundance[survey_week_val - 1]
    st.caption(f"📍 Currently active target survey week is **Week {survey_week_val}** (Relative Seasonal Presence: **{curr_val*100:.1f}%**). The red vertical marker highlights the active week position.")
    
    try:
        import altair as alt
        chart_data = pd.DataFrame({
            "Annual Week": list(range(1, 53)),
            "Relative Abundance": phen.weekly_abundance
        })
        base_line = alt.Chart(chart_data).mark_line(color="#02818a", strokeWidth=3).encode(
            x=alt.X("Annual Week:Q", title="Annual Week (1 to 52)"),
            y=alt.Y("Relative Abundance:Q", title="Relative Seasonal Abundance")
        )
        rule = alt.Chart(pd.DataFrame({"Annual Week": [survey_week_val]})).mark_rule(color="#e31a1c", strokeWidth=2, strokeDash=[4, 4]).encode(
            x="Annual Week:Q"
        )
        point = alt.Chart(pd.DataFrame({"Annual Week": [survey_week_val], "Relative Abundance": [curr_val]})).mark_point(color="#e31a1c", size=120, filled=True).encode(
            x="Annual Week:Q",
            y="Relative Abundance:Q"
        )
        st.altair_chart((base_line + rule + point).properties(height=320), use_container_width=True)
    except Exception:
        phen_df = pd.DataFrame({
            "Annual Week (1-52)": list(range(1, 53)),
            f"Seasonal Abundance ({sp_meta.common_name})": phen.weekly_abundance
        }).set_index("Annual Week (1-52)")
        st.line_chart(phen_df, color="#02818a")

# --- TAB 3: REDUNDANCY ATLAS & SPATIAL GRID ---
with tab_atlas:
    st.subheader("📊 Kansas City Equal-Area 3 km Spatial Grid")
    grid = EqualAreaGrid()
    atlas = RedundancyAtlas(grid)
    c1, c2 = st.columns(2)
    c1.metric("Total Grid Cells", f"{grid.total_cells}")
    c2.metric("Cell Resolution", f"{grid.resolution_km} km x {grid.resolution_km} km", "~9.0 km² per cell")

# --- TAB 4: MODEL CALIBRATION & OUT-OF-FOLD CV ---
with tab_models:
    st.subheader("🤖 Species Encounter Model Calibration & Out-of-Fold Spatial CV")
    st.caption("Status: Synthetic Demonstration (Real empirical model requires EBD dataset fitting)")
    cv_results = [
        {"Species Name": "Melospiza melodia (Song Sparrow)", "Out-of-Fold Brier Score": 0.2100, "Spatial AUC-ROC": 0.418, "Status": "Synthetic Demonstration"},
        {"Species Name": "Passerina cyanea (Indigo Bunting)", "Out-of-Fold Brier Score": 0.1850, "Spatial AUC-ROC": 0.720, "Status": "Synthetic Demonstration"},
        {"Species Name": "Cardinalis cardinalis (Northern Cardinal)", "Out-of-Fold Brier Score": 0.1244, "Spatial AUC-ROC": 0.646, "Status": "Synthetic Demonstration"}
    ]
    st.table(pd.DataFrame(cv_results))

# --- TAB 5: POLICY BENCHMARK COMPARISON ---
with tab_benchmark:
    st.subheader("⚔️ Policy Comparison: OVON vs. Raw Hotspot vs. Random")

    rand_sol = build_random_route(dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min), seed=42)
    hot_sol = build_hotspot_route(dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min))

    bench_df = pd.DataFrame([
        {"Policy": "1. Random Feasible", "Total Stops": len(rand_sol.sites), "Total Time (min)": rand_sol.total_time_minutes, "Multi-Species Utility": rand_sol.utility},
        {"Policy": "2. Raw Hotspot / Richness", "Total Stops": len(hot_sol.sites), "Total Time (min)": hot_sol.total_time_minutes, "Multi-Species Utility": hot_sol.utility},
        {"Policy": "3. OVON Information-Aware", "Total Stops": len(ovon_sol.sites), "Total Time (min)": ovon_sol.total_time_minutes, "Multi-Species Utility": ovon_sol.utility},
    ])

    st.table(bench_df)
    st.bar_chart(bench_df, x="Policy", y="Multi-Species Utility", color="Policy")
