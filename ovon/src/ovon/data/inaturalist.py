import math
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from ovon.synthetic.generator import ExistingObservation
from ovon.data.enviroatlas import fetch_enviroatlas_covariates, covariates_to_habitat_vector
from ovon.data.ebird import DataResult

@dataclass
class iNaturalistRecord:
    id: int
    species_name: str
    common_name: str
    lat: float
    lon: float
    observed_on: str
    week: int
    quality_grade: str  # "research"
    user_login: str
    image_url: Optional[str] = None
    uri: Optional[str] = None

# Demonstration Fixtures for iNaturalist Presence-Only Observations
DEMO_INATURALIST_OCCURRENCES: List[Dict[str, Any]] = [
    {
        "id": 101001,
        "species_name": "Passerina cyanea",
        "common_name": "Indigo Bunting",
        "lat": 39.0142,
        "lon": -94.3125,
        "observed_on": "2024-05-18",
        "week": 20,
        "quality_grade": "research",
        "user_login": "kc_birder_nature",
        "loc_name": "Burr Oak Woods Conservation Area (Blue Springs)"
    },
    {
        "id": 101002,
        "species_name": "Setophaga coronata",
        "common_name": "Yellow-rumped Warbler",
        "lat": 38.8921,
        "lon": -94.3821,
        "observed_on": "2024-05-02",
        "week": 18,
        "quality_grade": "research",
        "user_login": "naturalist_missouri",
        "loc_name": "James A. Reed Memorial Wildlife Area (Lee's Summit)"
    },
    {
        "id": 101003,
        "species_name": "Lophodytes cucullatus",
        "common_name": "Hooded Merganser",
        "lat": 39.3621,
        "lon": -94.6121,
        "observed_on": "2024-04-20",
        "week": 16,
        "quality_grade": "research",
        "user_login": "smithville_wildlife",
        "loc_name": "Smithville Lake Conservation Area (North)"
    },
    {
        "id": 101004,
        "species_name": "Passerina cyanea",
        "common_name": "Indigo Bunting",
        "lat": 38.6421,
        "lon": -94.8621,
        "observed_on": "2024-05-24",
        "week": 21,
        "quality_grade": "research",
        "user_login": "kansas_field_botany",
        "loc_name": "Hillsdale State Park & Wetlands (South)"
    }
]

# Legacy alias
FALLBACK_INAT_RECORDS = DEMO_INATURALIST_OCCURRENCES

def fetch_inaturalist_kc_occurrences(
    center_lat: float = 39.0997,
    center_lon: float = -94.5786,
    radius_km: float = 45.0,
    limit: int = 200,
    timeout: int = 5
) -> DataResult[iNaturalistRecord]:
    """
    Fetch research-grade bird observations across Greater Kansas City from iNaturalist Open API.
    Returns DataResult with provenance metadata.
    """
    url = "https://api.inaturalist.org/v1/observations"
    params = {
        "lat": center_lat,
        "lng": center_lon,
        "radius": radius_km,
        "iconic_taxa": "Aves",
        "quality_grade": "research",
        "per_page": limit,
        "order": "desc",
        "order_by": "created_at"
    }

    records: List[iNaturalistRecord] = []
    try:
        res = requests.get(url, params=params, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            for item in results:
                geojson = item.get("geojson", {})
                coords = geojson.get("coordinates", [])
                if len(coords) == 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    taxon = item.get("taxon", {})
                    obs_date = item.get("observed_on", "2024-05-18")
                    user = item.get("user", {}).get("login", "inat_user")
                    
                    try:
                        dt = obs_date.split("-")
                        month = int(dt[1])
                        day = int(dt[2])
                        week = min(52, max(1, int((month - 1) * 4.33 + day / 7.0)))
                    except Exception:
                        week = 18

                    photos = item.get("photos", [])
                    img_url = photos[0].get("url") if photos else None

                    records.append(iNaturalistRecord(
                        id=item.get("id", 0),
                        species_name=taxon.get("name", "Aves"),
                        common_name=taxon.get("preferred_common_name", taxon.get("name", "Bird")),
                        lat=lat,
                        lon=lon,
                        observed_on=obs_date,
                        week=week,
                        quality_grade=item.get("quality_grade", "research"),
                        user_login=user,
                        image_url=img_url,
                        uri=item.get("uri")
                    ))
            if records:
                return DataResult(
                    records=records,
                    source_name="iNaturalist API v1 research occurrences",
                    source_type="live_api"
                )
    except Exception:
        pass

    # Fallback to curated demo dataset
    for item in DEMO_INATURALIST_OCCURRENCES:
        records.append(iNaturalistRecord(
            id=item["id"],
            species_name=item["species_name"],
            common_name=item["common_name"],
            lat=item["lat"],
            lon=item["lon"],
            observed_on=item["observed_on"],
            week=item["week"],
            quality_grade=item["quality_grade"],
            user_login=item["user_login"]
        ))
    return DataResult(
        records=records,
        source_name="Curated Kansas City iNaturalist Demo Fixtures",
        source_type="curated_demo",
        warning="Using curated demo fixtures. Live API call unavailable."
    )

def fetch_inaturalist_kc_observations(
    center_lat: float = 39.0997,
    center_lon: float = -94.5786,
    radius_km: float = 45.0,
    limit: int = 200,
    timeout: int = 5
) -> List[iNaturalistRecord]:
    """Legacy helper returning list of records."""
    res = fetch_inaturalist_kc_occurrences(
        center_lat=center_lat, center_lon=center_lon, radius_km=radius_km, limit=limit, timeout=timeout
    )
    return res.records

def inaturalist_records_to_existing_observations(
    records: List[iNaturalistRecord],
    center_lat: float = 39.0997,
    center_lon: float = -94.5786
) -> List[ExistingObservation]:
    """
    Convert iNaturalist research-grade records into ExistingObservation objects.
    """
    existing_obs: List[ExistingObservation] = []
    for r in records:
        x_km = (r.lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
        y_km = (r.lat - center_lat) * 111.0
        
        covs = fetch_enviroatlas_covariates(r.lat, r.lon, location_name=r.common_name)
        hab_vec = covariates_to_habitat_vector(covs)

        obs = ExistingObservation(
            x_km=x_km,
            y_km=y_km,
            habitat=hab_vec,
            week=r.week,
            lat=r.lat,
            lon=r.lon,
            observer_id=f"iNat-{r.user_login}"
        )
        existing_obs.append(obs)

    return existing_obs
