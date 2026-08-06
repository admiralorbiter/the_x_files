from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Any, Optional, Literal
import numpy as np

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
    Tracks protocol, effort covariates, and explicit detection/non-detection status.
    """
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
    lat: float = 0.0
    lon: float = 0.0

def aggregate_species_evidence(
    evidence_records: List[SpeciesEvidence],
    cell_id: str,
    species_id: str,
    target_week: int,
    week_window: int = 4
) -> Dict[str, Any]:
    """
    Aggregate checklist effort, detections, and calculate local coverage score C(s, i, t) in [0, 1).
    """
    cell_records = [
        r for r in evidence_records
        if r.cell_id == cell_id and abs(r.week - target_week) <= week_window
    ]
    sp_records = [r for r in cell_records if r.species_id == species_id]

    n_checklists = len([r for r in cell_records if "complete_checklist" in r.evidence_type])
    n_detections = len([r for r in sp_records if r.detection is True])
    n_nondetections = len([r for r in sp_records if r.detection is False])
    recent_occurrences = len([r for r in sp_records if r.evidence_type in ("presence_only", "photo_verified_presence")])

    # Effective coverage C(s, i, t) formula: diminishing returns on complete checklists
    coverage_score = 1.0 - np.exp(-0.40 * n_checklists)

    return {
        "cell_id": cell_id,
        "species_id": species_id,
        "target_week": target_week,
        "n_checklists": n_checklists,
        "n_detections": n_detections,
        "n_nondetections": n_nondetections,
        "recent_occurrences": recent_occurrences,
        "coverage_score": float(coverage_score)
    }
