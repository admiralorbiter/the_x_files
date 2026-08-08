from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Literal, Tuple
import numpy as np
from ovon.utility.metrics import temporal_cyclic_distance
from ovon.data.species_enrichment import get_canonical_taxon, TaxonRef

EvidenceType = Literal[
    "complete_checklist_detection",
    "complete_checklist_nondetection",
    "presence_only",
    "photo_verified_presence"
]

@dataclass(frozen=True)
class SpeciesEvidence:
    """
    Decoupled species-aware ecological evidence record.
    Tracks unique event_id, protocol, effort covariates, canonical taxon_id, and detection status.
    """
    event_id: str
    species_id: str
    cell_id: str
    observation_date: date
    week: int
    source: str
    evidence_type: EvidenceType
    taxon_id: str = ""
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    observer_count: Optional[int] = None
    detection: Optional[bool] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

    def __post_init__(self):
        if not self.taxon_id and self.species_id:
            object.__setattr__(self, "taxon_id", get_canonical_taxon(self.species_id).taxon_id)

def parse_source_date(raw_date: Any, default_week: int = 18) -> Tuple[date, int]:
    """Parse raw source date into validated date and annual week number."""
    if isinstance(raw_date, date):
        return raw_date, raw_date.isocalendar().week
    if isinstance(raw_date, str) and raw_date:
        try:
            clean_str = raw_date.split("T")[0].strip()
            dt = date.fromisoformat(clean_str)
            return dt, dt.isocalendar().week
        except ValueError:
            pass
    today = date.today()
    return today, default_week

def assign_cell(grid: Any, lat: Optional[float], lon: Optional[float], site_id: Optional[Any] = None) -> str:
    """Assign spatial cell_id using grid.assign_point(lat, lon) or explicit site_id."""
    if grid is not None and lat is not None and lon is not None:
        if hasattr(grid, "assign_point"):
            c = grid.assign_point(lat, lon)
            if c is not None:
                return f"cell_{c}"
        elif hasattr(grid, "get_cell_id"):
            c = grid.get_cell_id(lat, lon)
            if c is not None:
                return str(c) if str(c).startswith("cell_") else f"cell_{c}"
    if site_id is not None:
        return f"cell_{site_id}"
    return "cell_0"

def aggregate_species_evidence(
    evidence_records: List[SpeciesEvidence],
    cell_id: str,
    species_id: str,
    target_week: int,
    week_window: int = 4
) -> Dict[str, Any]:
    """
    Aggregate checklist effort, detections, and calculate local coverage score C(s, i, t) in [0, 1).
    Deduplicates complete checklists by unique event_id and uses cyclic annual week distance.
    Uses canonical taxon_id matching so common and scientific species names match seamlessly.
    """
    target_taxon_id = get_canonical_taxon(species_id).taxon_id

    cell_records = [
        r for r in evidence_records
        if r.cell_id == cell_id and temporal_cyclic_distance(r.week, target_week) <= week_window
    ]
    sp_records = [
        r for r in cell_records
        if getattr(r, "taxon_id", get_canonical_taxon(r.species_id).taxon_id) == target_taxon_id
    ]

    # Deduplicate complete checklist count by unique event_id
    complete_checklist_ids = {
        r.event_id for r in cell_records if "complete_checklist" in r.evidence_type
    }
    n_checklists = len(complete_checklist_ids)

    # Deduplicate detections and non-detections by unique event_id
    detection_event_ids = {r.event_id for r in sp_records if r.detection is True}
    nondetection_event_ids = {r.event_id for r in sp_records if r.detection is False}

    # Detect contradictions where the same event contains both detection and non-detection
    contradictions = detection_event_ids.intersection(nondetection_event_ids)
    if contradictions:
        nondetection_event_ids = nondetection_event_ids - contradictions

    n_detections = len(detection_event_ids)
    n_nondetections = len(nondetection_event_ids)

    recent_occurrences = len([
        r for r in sp_records
        if r.evidence_type in ("presence_only", "photo_verified_presence")
        or (r.evidence_type == "complete_checklist_detection" and r.detection is True)
    ])

    # Diminishing returns coverage score C(s, i, t)
    coverage_score = 1.0 - np.exp(-0.40 * n_checklists)

    return {
        "cell_id": cell_id,
        "species_id": species_id,
        "taxon_id": target_taxon_id,
        "target_week": target_week,
        "n_checklists": n_checklists,
        "n_detections": n_detections,
        "n_nondetections": n_nondetections,
        "recent_occurrences": recent_occurrences,
        "has_contradictions": len(contradictions) > 0,
        "contradiction_count": len(contradictions),
        "coverage_score": float(coverage_score)
    }

def build_species_evidence(
    ebird_events: Optional[List[Dict[str, Any]]] = None,
    ebird_detections: Optional[List[Dict[str, Any]]] = None,
    gbif_occurrences: Optional[List[Dict[str, Any]]] = None,
    inat_occurrences: Optional[List[Dict[str, Any]]] = None,
    grid: Any = None
) -> List[SpeciesEvidence]:
    """
    Adapter building normalized SpeciesEvidence records from multi-source observations.
    Correctly classifies eBird recent occurrences as presence_only (reserving complete_checklist for validated EBD data).
    Parses exact source dates and assigns real spatial cell_ids.
    """
    records: List[SpeciesEvidence] = []

    # 1. Process GBIF presence occurrences
    if gbif_occurrences:
        for idx, r in enumerate(gbif_occurrences):
            sp_raw = r.get("species") or r.get("species_id") or "Unknown species"
            taxon = get_canonical_taxon(sp_raw)
            lat = r.get("lat") or r.get("decimalLatitude")
            lon = r.get("lon") or r.get("decimalLongitude")
            obs_date, week = parse_source_date(r.get("event_date") or r.get("eventDate") or r.get("observation_date"), default_week=int(r.get("week", 18)))
            cell_id = r.get("cell_id") or assign_cell(grid, float(lat) if lat is not None else None, float(lon) if lon is not None else None, site_id=r.get("site_id"))

            records.append(SpeciesEvidence(
                event_id=str(r.get("event_id", f"gbif_evt_{idx}")),
                species_id=taxon.common_name,
                taxon_id=taxon.taxon_id,
                cell_id=str(cell_id),
                observation_date=obs_date,
                week=week,
                source="GBIF",
                evidence_type="presence_only",
                detection=None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    # 2. Process eBird sightings / recent occurrences
    if ebird_detections:
        for idx, r in enumerate(ebird_detections):
            sp_raw = r.get("species") or r.get("species_id") or "Unknown species"
            taxon = get_canonical_taxon(sp_raw)
            lat = r.get("lat")
            lon = r.get("lon")
            obs_date, week = parse_source_date(r.get("obsDt") or r.get("observation_date"), default_week=int(r.get("week", 18)))
            evt_id = str(r.get("event_id", f"ebird_evt_{idx}"))
            
            # Check if record is a validated complete checklist or a recent occurrence
            is_complete = bool(r.get("effort_completed", False) or r.get("complete_checklist", False))
            det = bool(r.get("detection", True))

            if is_complete:
                ev_type: EvidenceType = "complete_checklist_detection" if det else "complete_checklist_nondetection"
            else:
                ev_type = "presence_only"

            cell_id = r.get("cell_id") or assign_cell(grid, float(lat) if lat is not None else None, float(lon) if lon is not None else None, site_id=r.get("site_id"))

            records.append(SpeciesEvidence(
                event_id=evt_id,
                species_id=taxon.common_name,
                taxon_id=taxon.taxon_id,
                cell_id=str(cell_id),
                observation_date=obs_date,
                week=week,
                source="eBird Recent Occurrence" if not is_complete else "eBird EBD Checklist",
                evidence_type=ev_type,
                duration_minutes=float(r.get("duration_minutes", 15.0)),
                detection=det if is_complete else None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    # 3. Process iNaturalist photo-verified occurrences
    if inat_occurrences:
        for idx, r in enumerate(inat_occurrences):
            sp_raw = r.get("species_name") or r.get("species") or r.get("species_id") or "Unknown species"
            taxon = get_canonical_taxon(sp_raw)
            lat = r.get("lat") or r.get("latitude")
            lon = r.get("lon") or r.get("longitude")
            obs_date, week = parse_source_date(r.get("observed_on") or r.get("observation_date"), default_week=int(r.get("week", 18)))
            cell_id = r.get("cell_id") or assign_cell(grid, float(lat) if lat is not None else None, float(lon) if lon is not None else None, site_id=r.get("site_id"))

            records.append(SpeciesEvidence(
                event_id=str(r.get("event_id", f"inat_evt_{idx}")),
                species_id=taxon.common_name,
                taxon_id=taxon.taxon_id,
                cell_id=str(cell_id),
                observation_date=obs_date,
                week=week,
                source="iNaturalist",
                evidence_type="photo_verified_presence",
                detection=None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    return records
