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
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.features.grid import EqualAreaGrid
from ovon.features.redundancy import RedundancyAtlas
from ovon.routing.optimizer import (
    build_greedy_route,
    refine_route_local_search,
    build_random_route,
    build_hotspot_route
)

st.set_page_config(
    page_title="OVON - Optimal Volunteer Observation Network",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🦅 OVON: Optimal Volunteer Observation Network")
st.caption("Human-Aware, Route-Constrained Multi-Species Adaptive Sampling — Greater Kansas City Pilot Region")

# Fetch GBIF species records for filtering and analytics
@st.cache_data
def get_cached_gbif_records():
    return fetch_gbif_kc_birds(limit=200)

gbif_records = get_cached_gbif_records()
all_gbif_species = sorted(list(set([r["species"] for r in gbif_records if r.get("species")])))

# Sidebar Configuration
st.sidebar.header("⚙️ Optimization Parameters")

use_real_kc = st.sidebar.toggle("Use Real Kansas City Parks & GBIF Records", value=True)

st.sidebar.subheader("🦅 Species Map Filter")
show_gbif_layer = st.sidebar.checkbox("Overlay GBIF Species Sightings on Map", value=True)
selected_species_filter = st.sidebar.selectbox("Filter Map by Species", options=["All Species"] + all_gbif_species)

if use_real_kc:
    @st.cache_data
    def load_real_dataset():
        return build_kc_real_dataset()
    dataset = load_real_dataset()
else:
    @st.cache_data
    def load_synthetic_dataset():
        return generate_synthetic_dataset(n_sites=40, seed=42)
    dataset = load_synthetic_dataset()

# Park Selection for Starting Node
site_names = [getattr(s, "park_name", f"Candidate Site {s.site_id}") for s in dataset.candidate_sites]
start_site_idx = st.sidebar.selectbox("Starting Location / Hub", options=range(len(site_names)), format_func=lambda i: site_names[i])

budget_min = st.sidebar.slider("Total Route Time Budget (minutes)", min_value=30, max_value=180, value=90, step=15)
lambda_red = st.sidebar.slider("Redundancy Penalty Weight (λ)", min_value=0.0, max_value=2.0, value=0.5, step=0.1)

# Run OVON Optimizer
greedy_sol = build_greedy_route(dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min), lambda_redundancy=lambda_red)
ovon_sol = refine_route_local_search(greedy_sol, dataset, lambda_redundancy=lambda_red)

# Tabs Layout
tab_map, tab_species, tab_atlas, tab_benchmark = st.tabs([
    "🗺️ Route Map & Species Layer",
    "🦅 Species Analytics & GBIF Records",
    "📊 Redundancy Atlas & Spatial Grid",
    "⚔️ Policy Benchmark Comparison"
])

# Color palette for species
SPECIES_COLORS = ["#e31a1c", "#1f78b4", "#33a02c", "#ff7f00", "#6a3d9a", "#a6cee3", "#b2df8a", "#fdbf6f"]
species_color_map = {sp: SPECIES_COLORS[idx % len(SPECIES_COLORS)] for idx, sp in enumerate(all_gbif_species)}

# --- TAB 1: ROUTE MAP & SPECIES LAYER ---
with tab_map:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Route Time", f"{ovon_sol.total_time_minutes:.1f} min", f"Budget: {budget_min} min")
    col2.metric("Driving Travel Time", f"{ovon_sol.total_travel_minutes:.1f} min")
    col3.metric("Stationary Survey Time", f"{ovon_sol.total_observation_minutes:.1f} min", f"{len(ovon_sol.sites)} Stops")
    col4.metric("Multi-Species Utility", f"{ovon_sol.utility:.4f}")

    # Map Rendering
    center_lat = getattr(dataset.candidate_sites[0], "lat", 39.0997)
    center_lon = getattr(dataset.candidate_sites[0], "lon", -94.5786)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Plot GBIF species sighting points with species-specific colors & popups
    if show_gbif_layer:
        filtered_gbif = gbif_records
        if selected_species_filter != "All Species":
            filtered_gbif = [r for r in gbif_records if r.get("species") == selected_species_filter]

        for r in filtered_gbif:
            sp_name = r.get("species", "Unknown Bird")
            color = species_color_map.get(sp_name, "#e31a1c")
            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 13px;">
                <b style="color: {color}; font-size: 14px;">🦅 {sp_name}</b><br>
                <b>Date:</b> {r.get('event_date', '2024')}<br>
                <b>Lat/Lon:</b> {r['lat']:.4f}, {r['lon']:.4f}<br>
                <span style="color: #666;">Source: GBIF Biodiversity Record</span>
            </div>
            """
            folium.CircleMarker(
                location=[r["lat"], r["lon"]],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)

    # Plot all candidate sites in blue
    for s in dataset.candidate_sites:
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
        park_name = getattr(s, "park_name", f"Site {s.site_id}")

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color="#3388ff",
            fill=True,
            fill_color="#3388ff",
            fill_opacity=0.7,
            popup=f"<b>{park_name}</b><br>Candidate Park #{s.site_id}"
        ).add_to(m)

    # Plot selected route stops in green with sequence badges
    route_coords = []
    for idx, s in enumerate(ovon_sol.sites):
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        route_coords.append([lat, lon])

        folium.Marker(
            location=[lat, lon],
            popup=f"<b>Stop {idx+1}: {park_name}</b><br>Protocol: 10-min stationary complete checklist",
            icon=folium.Icon(color="green" if idx > 0 else "blue", icon="info-sign")
        ).add_to(m)

    # Draw polyline connecting stops
    if len(route_coords) > 1:
        folium.PolyLine(route_coords, color="#2b8cbe", weight=4, opacity=0.9).add_to(m)

    if HAS_STREAMLIT_FOLIUM:
        st_folium(m, width=1200, height=500)
    else:
        st.components.v1.html(m._repr_html_(), height=500)

    st.subheader("📋 Volunteer Route Itinerary & Protocol")
    itinerary_data = []
    for idx, s in enumerate(ovon_sol.sites):
        park_name = getattr(s, "park_name", f"Candidate Site {s.site_id}")
        lat = getattr(s, "lat", center_lat + (s.y / 111.0))
        lon = getattr(s, "lon", center_lon + (s.x / (111.0 * 0.77)))
        itinerary_data.append({
            "Stop #": idx + 1,
            "Location Name": park_name,
            "Coordinates": f"{lat:.4f}, {lon:.4f}",
            "Required Protocol": "10-minute stationary complete eBird checklist",
            "Survey Duration": f"{s.observation_minutes} min"
        })
    st.table(pd.DataFrame(itinerary_data))

# --- TAB 2: SPECIES ANALYTICS & GBIF RECORDS ---
with tab_species:
    st.subheader("🦅 Focal Species Portfolio & GBIF Occurrence Analytics")
    st.markdown("""
    OVON optimizes multi-species information utility across focal species. Below is a detailed breakdown of bird species detections across Kansas City.
    """)

    sp_col1, sp_col2 = st.columns([1, 2])

    with sp_col1:
        st.subheader("Focal Portfolio Target Weights")
        species_df = pd.DataFrame({
            "Species ID": [f"SP-{i+1:02d}" for i in range(dataset.n_species)],
            "Focal Species Name": dataset.species_names,
            "Utility Weight ($w_s$)": [f"{1.0 / dataset.n_species:.3f}" for _ in range(dataset.n_species)]
        })
        st.table(species_df)

    with sp_col2:
        st.subheader("📊 Kansas City Bird Species Detection Counts")
        gbif_df = pd.DataFrame(gbif_records)
        if "species" in gbif_df.columns:
            counts = gbif_df["species"].value_counts().reset_index()
            counts.columns = ["Species Name", "Detection Records"]
            st.bar_chart(counts, x="Species Name", y="Detection Records", color="Species Name")

    st.subheader("📋 Raw GBIF Sighting Data Table")
    st.dataframe(gbif_df, use_container_width=True)

# --- TAB 3: REDUNDANCY ATLAS & SPATIAL GRID ---
with tab_atlas:
    st.subheader("📊 Kansas City Equal-Area 3 km Spatial Grid")
    grid = EqualAreaGrid()
    atlas = RedundancyAtlas(grid)

    obs_list = [
        {
            "lat": grid.center_lat + (obs[1] / 111.0),
            "lon": grid.center_lon + (obs[0] / (111.0 * 0.77)),
            "week": obs[3],
            "observer_id": "obs_sample",
            "habitat": obs[2]
        }
        for obs in dataset.existing_observations
    ]
    atlas.ingest_observations(obs_list)
    top_undersampled = atlas.get_top_undersampled_cells(week=18, top_k=10)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Grid Cells", f"{grid.total_cells}")
    c2.metric("Cell Resolution", f"{grid.resolution_km} km x {grid.resolution_km} km", "~9.0 km² per cell")
    c3.metric("Historical Observational Events", f"{len(dataset.existing_observations)}")

    st.subheader("🎯 Priority Under-Observed Spatial Cells (Spring Migration - Week 18)")
    atlas_table = []
    for rank, (cell, metric) in enumerate(top_undersampled, 1):
        atlas_table.append({
            "Priority Rank": rank,
            "Cell ID": f"#{cell.cell_id}",
            "Grid Position": f"Row {cell.row}, Col {cell.col}",
            "Center Coordinate": f"{cell.center_lat:.4f}, {cell.center_lon:.4f}",
            "Checklists Recorded": metric.n_checklists,
            "Effective Coverage Score": f"{metric.effective_coverage:.4f}",
            "Redundancy Index R(a|D)": f"{metric.redundancy_index:.4f}"
        })
    st.dataframe(pd.DataFrame(atlas_table), use_container_width=True)

# --- TAB 4: POLICY BENCHMARK COMPARISON ---
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

    st.subheader("📈 Multi-Species Utility Score Comparison")
    st.bar_chart(bench_df, x="Policy", y="Multi-Species Utility", color="Policy")
