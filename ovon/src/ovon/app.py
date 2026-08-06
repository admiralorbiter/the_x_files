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
import altair as alt

try:
    from streamlit_folium import st_folium
    HAS_STREAMLIT_FOLIUM = True
except ImportError:
    HAS_STREAMLIT_FOLIUM = False

from ovon.data.fetch_public import build_kc_real_dataset, fetch_gbif_kc_birds
from ovon.data.ebird import fetch_recent_ebird_occurrences
from ovon.data.inaturalist import fetch_inaturalist_kc_occurrences
from ovon.data.fetch_urban import build_kc_urban_pedestrian_dataset
from ovon.data.enviroatlas import fetch_enviroatlas_covariates
from ovon.data.phenology import get_species_phenology, get_weekly_species_weights
from ovon.synthetic.generator import generate_synthetic_dataset
from ovon.features.grid import EqualAreaGrid
from ovon.features.redundancy import RedundancyAtlas
from ovon.data.evidence import SpeciesEvidence, build_species_evidence
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
from ovon.data.species_enrichment import get_enriched_species_metadata, get_canonical_taxon, TaxonRef

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

CACHE_VERSION = "v12_gbif_dataset_expansion"

@st.cache_data(ttl=3600)
def load_cached_gbif_records(cache_ver: str = CACHE_VERSION):
    return fetch_gbif_kc_birds(limit=200)

@st.cache_data(ttl=3600)
def load_cached_ebird_records(cache_ver: str = CACHE_VERSION):
    res = fetch_recent_ebird_occurrences()
    return res.records

@st.cache_data(ttl=3600)
def load_cached_inat_records(cache_ver: str = CACHE_VERSION):
    res = fetch_inaturalist_kc_occurrences()
    return res.records

gbif_records = load_cached_gbif_records(CACHE_VERSION)
ebird_records = load_cached_ebird_records(CACHE_VERSION)
inat_records = load_cached_inat_records(CACHE_VERSION)

all_gbif_species = sorted(list(set([r["species"] for r in gbif_records if isinstance(r, dict) and r.get("species")])))
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

    if show_gbif_layer and gbif_records:
        for rec in gbif_records:
            rec_sp = rec.get("species") if isinstance(rec, dict) else getattr(rec, "species", None)
            rec_taxon_id = get_canonical_taxon(rec_sp).taxon_id if rec_sp else None
            if selected_species_filter != "All Species":
                target_tx_id = get_canonical_taxon(selected_species_filter).taxon_id
                if rec_taxon_id != target_tx_id:
                    continue
            r_lat = rec.get("lat") if isinstance(rec, dict) else getattr(rec, "lat", None)
            r_lon = rec.get("lon") if isinstance(rec, dict) else getattr(rec, "lon", None)
            if r_lat is not None and r_lon is not None:
                sp_color = species_color_map.get(rec_sp, "#e31a1c")
                folium.CircleMarker(
                    location=[r_lat, r_lon], radius=4, color=sp_color, fill=True, fill_color=sp_color, fill_opacity=0.6,
                    popup=f"<b>GBIF Sighting</b>: {rec_sp or 'Sighting'}"
                ).add_to(m)

    if show_ebird_layer and ebird_records:
        for rec in ebird_records:
            r_lat = getattr(rec, "lat", None) if hasattr(rec, "lat") else (rec.get("lat") if isinstance(rec, dict) else None)
            r_lon = getattr(rec, "lon", None) if hasattr(rec, "lon") else (rec.get("lon") if isinstance(rec, dict) else None)
            sp_list = getattr(rec, "species_list", []) if hasattr(rec, "species_list") else (rec.get("species_list", []) if isinstance(rec, dict) else [])
            loc_name = getattr(rec, "loc_name", "eBird Location") if hasattr(rec, "loc_name") else (rec.get("loc_name", "eBird Location") if isinstance(rec, dict) else "eBird Location")
            
            if selected_species_filter != "All Species":
                target_tx_id = get_canonical_taxon(selected_species_filter).taxon_id
                list_tx_ids = [get_canonical_taxon(s).taxon_id for s in sp_list]
                if target_tx_id not in list_tx_ids:
                    continue

            if r_lat is not None and r_lon is not None:
                folium.Marker(
                    location=[r_lat, r_lon],
                    popup=f"<b>eBird Recent Occurrence</b>: {loc_name}<br>Species count: {len(sp_list)}",
                    icon=folium.Icon(color="purple", icon="flag")
                ).add_to(m)

    if show_inat_layer and inat_records:
        for rec in inat_records:
            rec_sp = getattr(rec, "species_name", None) if hasattr(rec, "species_name") else (rec.get("species_name") if isinstance(rec, dict) else None)
            rec_taxon_id = get_canonical_taxon(rec_sp).taxon_id if rec_sp else None
            if selected_species_filter != "All Species":
                target_tx_id = get_canonical_taxon(selected_species_filter).taxon_id
                if rec_taxon_id != target_tx_id:
                    continue
            r_lat = getattr(rec, "lat", None) if hasattr(rec, "lat") else (rec.get("lat") if isinstance(rec, dict) else None)
            r_lon = getattr(rec, "lon", None) if hasattr(rec, "lon") else (rec.get("lon") if isinstance(rec, dict) else None)
            comm_name = getattr(rec, "common_name", rec_sp) if hasattr(rec, "common_name") else (rec.get("common_name", rec_sp) if isinstance(rec, dict) else rec_sp)
            if r_lat is not None and r_lon is not None:
                folium.CircleMarker(
                    location=[r_lat, r_lon], radius=5, color="#e6550d", fill=True, fill_color="#fdae6b", fill_opacity=0.8,
                    popup=f"<b>iNaturalist Research-Grade</b>: {comm_name} ({rec_sp})"
                ).add_to(m)

    if heatmap_layer != "None":
        for s in dataset.candidate_sites:
            lat, lon = site_lat_lon(s, center_lat, center_lon)
            if heatmap_layer == "Epistemic Disagreement (QBC)":
                qbc = getattr(s, "qbc_scores", [0.35])
                val = float(np.mean(qbc)) if qbc is not None else 0.35
                color = "#990000" if val > 0.4 else "#ff7f00"
            else:
                p_vec = getattr(s, "true_p", [0.3])
                val = float(np.mean(p_vec)) if p_vec is not None else 0.3
                color = "#006d2c" if val > 0.4 else "#74c476"
            folium.CircleMarker(
                location=[lat, lon], radius=max(3, int(val * 15)), color=color, fill=True, fill_color=color, fill_opacity=0.4,
                popup=f"<b>{heatmap_layer}</b>: {val:.3f}"
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

    ebird_dicts = [
        {"species": sp, "lat": getattr(r, "lat", 39.0), "lon": getattr(r, "lon", -94.5), "week": getattr(r, "week", 18), "detection": True, "event_id": getattr(r, "checklist_id", "eb1")}
        for r in ebird_records for sp in (getattr(r, "species_list", []) if hasattr(r, "species_list") else r.get("species_list", []))
    ]
    inat_dicts = [
        {"species": getattr(r, "species_name", "Unknown") if hasattr(r, "species_name") else r.get("species_name", "Unknown"), "lat": getattr(r, "lat", 39.0) if hasattr(r, "lat") else r.get("lat", 39.0), "lon": getattr(r, "lon", -94.5) if hasattr(r, "lon") else r.get("lon", -94.5), "week": getattr(r, "week", 18) if hasattr(r, "week") else r.get("week", 18), "event_id": f"inat_{getattr(r, 'id', 0) if hasattr(r, 'id') else r.get('id', 0)}"}
        for r in inat_records
    ]

    species_evidence_records = build_species_evidence(
        gbif_occurrences=gbif_records, ebird_detections=ebird_dicts, inat_occurrences=inat_dicts
    )

    opp_cells = calculate_opportunity_surface(
        dataset, species_id=search_sp, survey_week=survey_week_val, mode=search_mode_key,
        observer_profile=observer_profile, species_evidence=species_evidence_records
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
    st.caption("Illustrative heuristic based on proxy canopy and greenness values; not effort-corrected.")
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
    st.subheader("🦅 Focal Species Portfolio & Dynamic Weekly Phenology Analytics")
    st.caption("Inspect species taxonomy, Wikipedia field photography, habitat preference, and seasonal annual abundance curves.")

    selected_sp = st.selectbox("Select Focal Avian Species for Deep-Dive", options=dataset.species_names, index=0)
    meta = get_enriched_species_metadata(selected_sp)
    phen = get_species_phenology(selected_sp)

    col_img, col_info = st.columns([1, 2])

    with col_img:
        if meta.photo_url:
            st.image(meta.photo_url, caption=f"Photo: {meta.common_name} ({meta.scientific_name})", use_container_width=True)
        else:
            st.info(f"📸 Image preview: {meta.common_name}")

    with col_info:
        st.markdown(f"### {meta.common_name} (*{meta.scientific_name}*)")
        
        m_c1, m_c2, m_c3 = st.columns(3)
        m_c1.metric("Guild Class", meta.guild_class)
        m_c2.metric("Migratory Status", phen.migratory_status)
        cur_abun = phen.weekly_abundance[min(51, max(0, survey_week_val - 1))]
        m_c3.metric(f"Week {survey_week_val} Abundance", f"{cur_abun*100:.1f}%")

        st.markdown(f"**Primary Habitat**: {meta.primary_habitat}")
        st.markdown(f"**Field Description**: {meta.description}")
        if meta.wikipedia_url:
            st.markdown(f"📖 [View full species article on Wikipedia]({meta.wikipedia_url})")

    st.divider()
    st.subheader(f"📈 Annual Phenology & Relative Abundance Curve — {selected_sp}")
    st.caption(f"Shows seasonal occupancy curve over 52 annual weeks. Vertical focus is current Target Survey Week: **Week {survey_week_val}** (Relative Abundance: {cur_abun:.4f}).")

    weeks_arr = np.arange(1, 53)
    phen_chart_df = pd.DataFrame({
        "Week": weeks_arr,
        "Relative Abundance": phen.weekly_abundance
    })

    base_line = alt.Chart(phen_chart_df).mark_line(color="#02818a", strokeWidth=3).encode(
        x=alt.X("Week:Q", scale=alt.Scale(domain=[1, 52]), title="Annual Observation Week (1 - 52)"),
        y=alt.Y("Relative Abundance:Q", scale=alt.Scale(domain=[0, 1.05]), title="Relative Occupancy / Abundance")
    )

    base_area = alt.Chart(phen_chart_df).mark_area(color="#02818a", opacity=0.15).encode(
        x="Week:Q",
        y="Relative Abundance:Q"
    )

    # Active Target Week Highlight Marker
    target_point_df = pd.DataFrame({
        "Week": [survey_week_val],
        "Relative Abundance": [cur_abun],
        "Label": [f"📍 Target Week {survey_week_val} ({cur_abun*100:.1f}%)"]
    })

    rule_line = alt.Chart(target_point_df).mark_rule(color="#e31a1c", strokeDash=[4, 4], strokeWidth=2).encode(
        x="Week:Q"
    )

    point_marker = alt.Chart(target_point_df).mark_circle(color="#e31a1c", size=140).encode(
        x="Week:Q",
        y="Relative Abundance:Q",
        tooltip=["Week", "Relative Abundance", "Label"]
    )

    text_annotation = alt.Chart(target_point_df).mark_text(
        align="left", dx=10, dy=-12, color="#e31a1c", fontSize=13, fontWeight="bold"
    ).encode(
        x="Week:Q",
        y="Relative Abundance:Q",
        text="Label:N"
    )

    phen_altair_chart = (base_area + base_line + rule_line + point_marker + text_annotation).properties(
        height=340
    )
    st.altair_chart(phen_altair_chart, use_container_width=True)

    st.info(f"💡 **Peak Activity Weeks**: {', '.join([f'Week {w}' for w in phen.peak_weeks[:6]])}")

    st.divider()
    st.markdown(f"### 📅 Portfolio Active Weekly Utility Weights for Target Survey Week **{survey_week_val}**")
    computed_weights = get_weekly_species_weights(dataset.species_names, survey_week_val)
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
    rand_sol = build_random_route(
        dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min),
        lambda_redundancy=lambda_red, survey_week=survey_week_val, seed=42
    )
    hot_sol = build_hotspot_route(
        dataset, start_site_id=start_site_idx, budget_minutes=float(budget_min),
        lambda_redundancy=lambda_red, survey_week=survey_week_val
    )

    bench_df = pd.DataFrame([
        {"Policy": "1. Random Feasible", "Total Stops": len(rand_sol.sites), "Total Time (min)": rand_sol.total_time_minutes, "Multi-Species Utility": rand_sol.utility},
        {"Policy": "2. Raw Hotspot / Richness", "Total Stops": len(hot_sol.sites), "Total Time (min)": hot_sol.total_time_minutes, "Multi-Species Utility": hot_sol.utility},
        {"Policy": "3. OVON Information-Aware", "Total Stops": len(ovon_sol.sites), "Total Time (min)": ovon_sol.total_time_minutes, "Multi-Species Utility": ovon_sol.utility},
    ])

    st.table(bench_df)
    st.bar_chart(bench_df, x="Policy", y="Multi-Species Utility", color="Policy")
