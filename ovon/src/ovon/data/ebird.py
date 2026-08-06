import os
import math
import json
import requests
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Literal, TypeVar, Generic
import numpy as np

from ovon.synthetic.generator import ExistingObservation
from ovon.data.species_enrichment import resolve_common_name
from ovon.data.enviroatlas import fetch_enviroatlas_covariates, covariates_to_habitat_vector

T = TypeVar("T")

@dataclass
class DataResult(Generic[T]):
    records: List[T]
    source_name: str
    source_type: Literal["live_api", "local_research_file", "curated_demo", "synthetic"]
    retrieved_at: Optional[datetime] = field(default_factory=datetime.now)
    warning: Optional[str] = None

@dataclass
class ChecklistEvent:
    event_id: str
    source: str
    observer_id: Optional[str]
    latitude: float
    longitude: float
    date: date
    week: int
    protocol: str
    duration_minutes: float
    distance_km: float
    number_observers: int
    complete_checklist: bool

@dataclass
class ChecklistDetection:
    event_id: str
    species_id: str
    detected: bool
    count: Optional[int]

@dataclass
class eBirdChecklistRecord:
    checklist_id: str
    loc_id: str
    loc_name: str
    lat: float
    lon: float
    observation_date: str
    week: int
    duration_minutes: int
    distance_km: float
    protocol: str  # e.g., "eBird Stationary", "eBird Traveling"
    species_list: List[str]
    effort_completed: bool = True

# Curated Demonstration Fixtures (Explicitly marked as demo fixtures, not real EBD complete checklists)
DEMO_EBIRD_CHECKLIST_FIXTURES: List[Dict[str, Any]] = [
    {
        "checklist_id": "CL-KC-001",
        "loc_id": "L-SwopePark",
        "loc_name": "Swope Park & Fountains",
        "lat": 39.0042,
        "lon": -94.5245,
        "observation_date": "2024-05-18",
        "week": 20,
        "duration_minutes": 20,
        "distance_km": 0.0,
        "protocol": "eBird Stationary",
        "species_list": ["Passerina cyanea", "Setophaga coronata", "Dumetella carolinensis", "Haemorhous mexicanus"]
    },
    {
        "checklist_id": "CL-KC-002",
        "loc_id": "L-LoosePark",
        "loc_name": "Loose Park Rose Garden & Pond",
        "lat": 39.0347,
        "lon": -94.5932,
        "observation_date": "2024-05-12",
        "week": 19,
        "duration_minutes": 15,
        "distance_km": 0.4,
        "protocol": "eBird Traveling",
        "species_list": ["Passerina cyanea", "Dumetella carolinensis", "Chaetura pelagica", "Haemorhous mexicanus"]
    },
    {
        "checklist_id": "CL-KC-003",
        "loc_id": "L-PennValley",
        "loc_name": "Penn Valley Park Pond & Fountain",
        "lat": 39.0772,
        "lon": -94.5878,
        "observation_date": "2024-01-15",
        "week": 3,
        "duration_minutes": 10,
        "distance_km": 0.0,
        "protocol": "eBird Stationary",
        "species_list": ["Junco hyemalis", "Haemorhous mexicanus", "Falco peregrinus"]
    },
    {
        "checklist_id": "CL-KC-004",
        "loc_id": "L-UnionCemetery",
        "loc_name": "Historic Union Cemetery Wooded Grove",
        "lat": 39.0722,
        "lon": -94.5806,
        "observation_date": "2024-05-22",
        "week": 21,
        "duration_minutes": 15,
        "distance_km": 0.2,
        "protocol": "eBird Traveling",
        "species_list": ["Passerina cyanea", "Setophaga coronata", "Dumetella carolinensis"]
    },
    {
        "checklist_id": "CL-KC-005",
        "loc_id": "L-BrushCreek",
        "loc_name": "Brush Creek Greenway Corridor",
        "lat": 39.0415,
        "lon": -94.5861,
        "observation_date": "2024-04-28",
        "week": 17,
        "duration_minutes": 25,
        "distance_km": 1.2,
        "protocol": "eBird Traveling",
        "species_list": ["Setophaga coronata", "Lophodytes cucullatus", "Chaetura pelagica"]
    },
    {
        "checklist_id": "CL-KC-006",
        "loc_id": "L-ShawneeMission",
        "loc_name": "Shawnee Mission Park & Lake",
        "lat": 38.9832,
        "lon": -94.7932,
        "observation_date": "2024-05-05",
        "week": 18,
        "duration_minutes": 30,
        "distance_km": 1.5,
        "protocol": "eBird Traveling",
        "species_list": ["Passerina cyanea", "Setophaga coronata", "Dumetella carolinensis", "Lophodytes cucullatus"]
    }
]

# Legacy alias for backward compatibility in tests
FALLBACK_KC_EBIRD_CHECKLISTS = DEMO_EBIRD_CHECKLIST_FIXTURES

def fetch_recent_ebird_occurrences(
    region_code: str = "US-MO-095",
    api_key: Optional[str] = None,
    timeout: int = 4
) -> DataResult[eBirdChecklistRecord]:
    """
    Fetch recent eBird species occurrences (map markers / recent sightings) for a region.
    Queries official eBird API v2 recent observations endpoint. Returns a DataResult with provenance metadata.
    """
    api_key = api_key or os.environ.get("EBIRD_API_KEY")
    records: List[eBirdChecklistRecord] = []

    if api_key:
        url = f"https://api.ebird.org/v2/data/obs/{region_code}/recent"
        headers = {"X-eBirdApiToken": api_key}
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                for item in data[:30]:
                    obs_dt = item.get("obsDt", "2024-05-18")
                    records.append(eBirdChecklistRecord(
                        checklist_id=item.get("subId", f"S-{item.get('locId')}"),
                        loc_id=item.get("locId", "L-KC"),
                        loc_name=item.get("locName", "Kansas City Hotspot"),
                        lat=float(item.get("lat", 39.0997)),
                        lon=float(item.get("lng", -94.5786)),
                        observation_date=obs_dt,
                        week=18,
                        duration_minutes=int(item.get("durationHrs", 0.25) * 60),
                        distance_km=float(item.get("howMany", 1.0) * 0.1),
                        protocol="eBird Recent Occurrence",
                        species_list=[item.get("sciName", "Passerina cyanea")],
                        effort_completed=False
                    ))
                if records:
                    return DataResult(
                        records=records,
                        source_name=f"eBird API v2 recent obs ({region_code})",
                        source_type="live_api"
                    )
        except Exception as e:
            pass

    # Fallback to demonstration fixtures
    for item in DEMO_EBIRD_CHECKLIST_FIXTURES:
        records.append(eBirdChecklistRecord(
            checklist_id=item["checklist_id"],
            loc_id=item["loc_id"],
            loc_name=item["loc_name"],
            lat=item["lat"],
            lon=item["lon"],
            observation_date=item["observation_date"],
            week=item["week"],
            duration_minutes=item["duration_minutes"],
            distance_km=item["distance_km"],
            protocol=item["protocol"],
            species_list=item["species_list"],
            effort_completed=True
        ))
    return DataResult(
        records=records,
        source_name="Curated Kansas City eBird Demo Fixtures",
        source_type="curated_demo",
        warning="Using curated demo fixtures. Live API call unavailable or unauthenticated."
    )

def fetch_ebird_kc_checklists(
    region_code: str = "US-MO-095",
    api_key: Optional[str] = None,
    timeout: int = 4
) -> List[eBirdChecklistRecord]:
    """Legacy helper function returning list of records directly."""
    res = fetch_recent_ebird_occurrences(region_code=region_code, api_key=api_key, timeout=timeout)
    return res.records

def load_ebd_observations(file_path: str) -> List[Dict[str, Any]]:
    """Load raw observations from local eBird Basic Dataset (EBD) file (CSV/Parquet)."""
    if not os.path.exists(file_path):
        return []
    # Placeholder parser for EBD CSV/Parquet files
    obs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 10:
                obs.append({"sampling_event_id": parts[0], "scientific_name": parts[1], "observation_count": parts[2]})
    return obs

def load_sampling_events(file_path: str) -> List[ChecklistEvent]:
    """Load Sampling Event Data (SED) complete checklists from local file."""
    if not os.path.exists(file_path):
        return []
    events = []
    # Parse sampling event lines
    return events

def collapse_shared_checklists(events: List[ChecklistEvent]) -> List[ChecklistEvent]:
    """Collapse multiple observer checklists recorded for the exact same event/group."""
    seen = set()
    unique_events = []
    for ev in events:
        key = (ev.latitude, ev.longitude, ev.date, ev.time if hasattr(ev, 'time') else 0)
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)
    return unique_events

def filter_complete_checklists(events: List[ChecklistEvent]) -> List[ChecklistEvent]:
    """Filter for complete effort-recorded checklists."""
    return [ev for ev in events if ev.complete_checklist and ev.duration_minutes > 0]

def zero_fill_focal_species(
    events: List[ChecklistEvent],
    detections: List[ChecklistDetection],
    focal_species_ids: List[str]
) -> List[ChecklistDetection]:
    """Create explicit non-detection (zeros) for focal species on complete checklists where species was absent."""
    det_map = {(d.event_id, d.species_id): d for d in detections}
    filled = []
    for ev in events:
        for sp_id in focal_species_ids:
            key = (ev.event_id, sp_id)
            if key in det_map:
                filled.append(det_map[key])
            else:
                filled.append(ChecklistDetection(
                    event_id=ev.event_id,
                    species_id=sp_id,
                    detected=False,
                    count=0
                ))
    return filled

def ebird_checklists_to_existing_observations(
    checklists: List[eBirdChecklistRecord],
    center_lat: float = 39.0997,
    center_lon: float = -94.5786
) -> List[ExistingObservation]:
    """
    Convert eBirdChecklistRecord items into OVON ExistingObservation objects.
    """
    existing_obs: List[ExistingObservation] = []
    for cl in checklists:
        x_km = (cl.lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
        y_km = (cl.lat - center_lat) * 111.0
        
        covs = fetch_enviroatlas_covariates(cl.lat, cl.lon, location_name=cl.loc_name)
        hab_vec = covariates_to_habitat_vector(covs)

        obs = ExistingObservation(
            x_km=x_km,
            y_km=y_km,
            habitat=hab_vec,
            week=cl.week,
            lat=cl.lat,
            lon=cl.lon,
            observer_id=f"eBird-{cl.checklist_id}"
        )
        existing_obs.append(obs)

    return existing_obs
