from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Optional, Literal
import numpy as np
from ovon.utility.metrics import temporal_cyclic_distance

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
    Tracks unique event_id, protocol, effort covariates, and explicit detection/non-detection status.
    """
    event_id: str
    species_id: str
    cell_id: str
    observation_date: date
    week: int
    source: str
    evidence_type: EvidenceType
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    observer_count: Optional[int] = None
    detection: Optional[bool] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

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
    Deduplicates detection and non-detection event IDs and flags contradictions.
    """
    cell_records = [
        r for r in evidence_records
        if r.cell_id == cell_id and temporal_cyclic_distance(r.week, target_week) <= week_window
    ]
    sp_records = [r for r in cell_records if r.species_id == species_id]

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
        # Resolve contradiction by favoring detection over non-detection for presence fitting
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
    Maps coordinates or site references to spatial cell_ids.
    """
    records: List[SpeciesEvidence] = []
    today = date.today()

    # 1. Process GBIF presence occurrences
    if gbif_occurrences:
        for idx, r in enumerate(gbif_occurrences):
            sp = r.get("species") or r.get("species_id") or "Unknown species"
            lat = r.get("lat") or r.get("decimalLatitude")
            lon = r.get("lon") or r.get("decimalLongitude")
            week = int(r.get("week", 18))
            cell_id = r.get("cell_id")
            if not cell_id:
                if grid is not None and lat is not None and lon is not None:
                    cell_id = getattr(grid, "get_cell_id", lambda lt, ln: f"cell_{idx}")(lat, lon)
                else:
                    cell_id = r.get("site_id", f"cell_{idx % 10}")
                if isinstance(cell_id, int):
                    cell_id = f"cell_{cell_id}"

            records.append(SpeciesEvidence(
                event_id=str(r.get("event_id", f"gbif_evt_{idx}")),
                species_id=str(sp),
                cell_id=str(cell_id),
                observation_date=today,
                week=week,
                source="GBIF",
                evidence_type="presence_only",
                detection=None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    # 2. Process eBird events / detections
    if ebird_detections:
        for idx, r in enumerate(ebird_detections):
            sp = r.get("species") or r.get("species_id") or "Unknown species"
            lat = r.get("lat")
            lon = r.get("lon")
            week = int(r.get("week", 18))
            evt_id = str(r.get("event_id", f"ebird_evt_{idx}"))
            det = bool(r.get("detection", True))
            ev_type: EvidenceType = "complete_checklist_detection" if det else "complete_checklist_nondetection"
            cell_id = r.get("cell_id")
            if not cell_id:
                if grid is not None and lat is not None and lon is not None:
                    cell_id = getattr(grid, "get_cell_id", lambda lt, ln: f"cell_{idx}")(lat, lon)
                else:
                    cell_id = r.get("site_id", f"cell_{idx % 10}")
                if isinstance(cell_id, int):
                    cell_id = f"cell_{cell_id}"

            records.append(SpeciesEvidence(
                event_id=evt_id,
                species_id=str(sp),
                cell_id=str(cell_id),
                observation_date=today,
                week=week,
                source="eBird",
                evidence_type=ev_type,
                duration_minutes=float(r.get("duration_minutes", 15.0)),
                detection=det,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    # 3. Process iNaturalist photo-verified occurrences
    if inat_occurrences:
        for idx, r in enumerate(inat_occurrences):
            sp = r.get("species") or r.get("species_id") or "Unknown species"
            lat = r.get("lat") or r.get("latitude")
            lon = r.get("lon") or r.get("longitude")
            week = int(r.get("week", 18))
            cell_id = r.get("cell_id")
            if not cell_id:
                if grid is not None and lat is not None and lon is not None:
                    cell_id = getattr(grid, "get_cell_id", lambda lt, ln: f"cell_{idx}")(lat, lon)
                else:
                    cell_id = r.get("site_id", f"cell_{idx % 10}")
                if isinstance(cell_id, int):
                    cell_id = f"cell_{cell_id}"

            records.append(SpeciesEvidence(
                event_id=str(r.get("event_id", f"inat_evt_{idx}")),
                species_id=str(sp),
                cell_id=str(cell_id),
                observation_date=today,
                week=week,
                source="iNaturalist",
                evidence_type="photo_verified_presence",
                detection=None,
                lat=float(lat) if lat is not None else None,
                lon=float(lon) if lon is not None else None
            ))

    return records
