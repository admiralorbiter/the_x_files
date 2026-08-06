import os
import math
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import requests

from ovon.synthetic.generator import CandidateSite, ExistingObservation, SyntheticDataset
from ovon.data.fetch_public import haversine_distance_km, fetch_gbif_kc_birds, DataFetchResult
from ovon.data.enviroatlas import fetch_enviroatlas_covariates, covariates_to_habitat_vector

# Curated Kansas City Urban Micro-Habitats, Transit Hubs & Pedestrian Greenways
FALLBACK_KC_URBAN_POIS = [
    {"name": "KC Streetcar Union Station Stop & Plaza", "lat": 39.0854, "lon": -94.5857, "type": "Transit Hub & Landmark Plaza", "transit_connection": "KC Streetcar", "habitat": [0.1, 0.2, 0.7]},
    {"name": "Penn Valley Park Pond & Firefighters Fountain", "lat": 39.0772, "lon": -94.5878, "type": "Urban Hilltop Park & Fountain", "transit_connection": "5 min walk from Main St Bus", "habitat": [0.4, 0.3, 0.3]},
    {"name": "Historic Union Cemetery Wooded Grove", "lat": 39.0722, "lon": -94.5806, "type": "Historic Cemetery & Mature Canopy", "transit_connection": "3 min walk from Main St Transit", "habitat": [0.7, 0.1, 0.2]},
    {"name": "Brush Creek Greenway & Cultural Plaza", "lat": 39.0415, "lon": -94.5861, "type": "Urban Riparian Corridor & Greenway Trail", "transit_connection": "Plaza Streetcar Line", "habitat": [0.3, 0.5, 0.2]},
    {"name": "J.C. Nichols Memorial Fountain & Mill Creek Trail", "lat": 39.0427, "lon": -94.5882, "type": "Fountain Plaza & Pedestrian Greenway", "transit_connection": "Plaza Transit Hub", "habitat": [0.2, 0.4, 0.4]},
    {"name": "Loose Park Rose Garden & Japanese Teahouse Pond", "lat": 39.0347, "lon": -94.5932, "type": "Urban Park, Arboretum & Pond", "transit_connection": "Main St MetroLink Bus", "habitat": [0.5, 0.3, 0.2]},
    {"name": "Trolley Track Trail (Brookside Greenway Corridor)", "lat": 39.0162, "lon": -94.5901, "type": "Rails-to-Trails Pedestrian Corridor", "transit_connection": "Brookside Bus Route", "habitat": [0.6, 0.1, 0.3]},
    {"name": "Berkley Riverfront Pedestrian Promenade", "lat": 39.1172, "lon": -94.5703, "type": "Riverfront Walkway & Wetlands", "transit_connection": "River Market Streetcar", "habitat": [0.2, 0.6, 0.2]},
    {"name": "Westport Historic Plaza & Pocket Garden", "lat": 39.0528, "lon": -94.5917, "type": "Urban Commercial Plaza & Green Pocket", "transit_connection": "Westport Bus Hub", "habitat": [0.2, 0.2, 0.6]},
    {"name": "River Market Square & Town Company Bluff Trail", "lat": 39.1098, "lon": -94.5833, "type": "Historic Public Square & River Overlook", "transit_connection": "River Market Streetcar", "habitat": [0.3, 0.3, 0.4]},
]

URBAN_FOCAL_SPECIES = [
    "Chimney Swift", "Peregrine Falcon", "Cedar Waxwing", "Common Nighthawk",
    "Yellow-rumped Warbler", "Indigo Bunting", "Northern Cardinal", "Black-capped Chickadee"
]

def fetch_kc_urban_pois_overpass(
    center_lat: float = 39.0854,
    center_lon: float = -94.5857,
    radius_km: float = 8.0,
    timeout: int = 10
) -> DataFetchResult:
    """
    Fetch urban pedestrian greenways, fountains, streetcar plazas, community gardens,
    and historic cemeteries across Kansas City via OpenStreetMap Overpass API.
    """
    radius_meters = int(radius_km * 1000)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:{timeout}];
    (
      node["highway"="pedestrian"](around:{radius_meters},{center_lat},{center_lon});
      node["leisure"="garden"](around:{radius_meters},{center_lat},{center_lon});
      node["historic"="cemetery"](around:{radius_meters},{center_lat},{center_lon});
      node["amenity"="fountain"](around:{radius_meters},{center_lat},{center_lon});
      node["tourism"="attraction"](around:{radius_meters},{center_lat},{center_lon});
    );
    out center 35;
    """

    try:
        response = requests.post(overpass_url, data={"data": query}, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            pois = []
            for el in elements:
                tags = el.get("tags", {})
                name = tags.get("name")
                if not name:
                    continue
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                poi_type = tags.get("amenity") or tags.get("leisure") or tags.get("highway") or "Urban POI"
                if lat and lon:
                    pois.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "type": poi_type.replace("_", " ").title(),
                        "transit_connection": "Urban Pedestrian Network",
                        "habitat": [0.33, 0.33, 0.34]
                    })
            if len(pois) >= 5:
                return DataFetchResult(
                    records=pois,
                    source="OpenStreetMap Overpass API (Urban Pedestrian)",
                    is_fallback=False
                )
    except Exception as e:
        pass

    return DataFetchResult(
        records=FALLBACK_KC_URBAN_POIS,
        source="Curated Kansas City Urban Micro-Habitats Demonstration Dataset",
        is_fallback=True,
        warning="OSM network fetch unavailable. Displaying curated Kansas City urban pedestrian POIs."
    )

def build_kc_urban_pedestrian_dataset(
    center_lat: float = 39.0854,
    center_lon: float = -94.5857,
    walking_speed_kmh: float = 4.5,
    trail_winding_factor: float = 1.25,
    n_bootstrap: int = 30,
    seed: int = 42
) -> SyntheticDataset:
    """
    Build a pedestrian urban candidate dataset anchored to Kansas City streetcar hubs,
    fountains, cemeteries, greenways, and 4.5 km/h walking travel matrices.
    """
    rng = np.random.default_rng(seed)
    fetch_res = fetch_kc_urban_pois_overpass(center_lat, center_lon)
    pois = fetch_res.records

    gbif_obs = fetch_gbif_kc_birds(center_lat, center_lon)
    species_list = sorted(list(set([o["species"] for o in gbif_obs if o.get("species")])))
    if len(species_list) < 4:
        species_list = URBAN_FOCAL_SPECIES
    species_list = species_list[:8]
    n_species = len(species_list)

    candidate_sites: List[CandidateSite] = []
    n_sites = len(pois)

    for i, poi in enumerate(pois):
        lat = poi["lat"]
        lon = poi["lon"]
        
        # Real EPA EnviroAtlas GIS environmental covariates
        covs = fetch_enviroatlas_covariates(lat, lon, location_name=poi.get("name"))
        hab = covariates_to_habitat_vector(covs)

        y_km = (lat - center_lat) * 111.0
        x_km = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))

        true_p = rng.uniform(0.15, 0.75, size=n_species)
        bootstrap_preds = np.zeros((n_species, n_bootstrap))
        for s in range(n_species):
            p_mean = true_p[s]
            bootstrap_preds[s] = np.clip(rng.normal(p_mean, 0.1, size=n_bootstrap), 0.01, 0.99)

        site = CandidateSite(
            site_id=i,
            x=x_km,
            y=y_km,
            habitat=hab,
            is_public=True,
            is_safe=True,
            observation_minutes=5,  # 5-min micro-stationary urban count
            true_p=true_p,
            bootstrap_predictions=bootstrap_preds,
            park_name=poi["name"],
            lat=lat,
            lon=lon,
            env_covariates=covs
        )
        # Store urban specific transit metadata
        site.transit_connection = poi.get("transit_connection", "Pedestrian Access")  # type: ignore
        candidate_sites.append(site)

    # Compute pedestrian walking travel time matrix (4.5 km/h speed)
    travel_time_matrix = np.zeros((n_sites, n_sites))
    for i in range(n_sites):
        for j in range(n_sites):
            if i == j:
                travel_time_matrix[i, j] = 0.0
            else:
                dist_direct = haversine_distance_km(pois[i]["lat"], pois[i]["lon"], pois[j]["lat"], pois[j]["lon"])
                dist_walking = dist_direct * trail_winding_factor
                travel_time_matrix[i, j] = (dist_walking / walking_speed_kmh) * 60.0

    existing_obs = [
        ExistingObservation(
            x_km=(o["lon"] - center_lon) * 111.0 * math.cos(math.radians(center_lat)),
            y_km=(o["lat"] - center_lat) * 111.0,
            habitat=np.array([0.25, 0.25, 0.25, 0.25]),
            week=18,
            lat=o.get("lat"),
            lon=o.get("lon")
        )
        for o in gbif_obs
    ]

    return SyntheticDataset(
        candidate_sites=candidate_sites,
        travel_time_matrix=travel_time_matrix,
        existing_observations=existing_obs,
        n_species=n_species,
        n_bootstrap=n_bootstrap,
        species_names=species_list
    )
