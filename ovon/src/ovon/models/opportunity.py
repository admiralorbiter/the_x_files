import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from ovon.data.phenology import get_species_phenology
from ovon.data.evidence import SpeciesEvidence, aggregate_species_evidence
from ovon.data.species_enrichment import get_canonical_taxon, TaxonRef
from ovon.features.habitat_analog import HabitatAnalogSearch
from ovon.utility.metrics import calculate_qbc_disagreement

SEARCH_MODES = {
    "likely_encounter": "1. Likely Encounter (Maximum Detection Index)",
    "expected_undocumented": "2. Expected but Undocumented (High Habitat Match + Low Survey Effort)",
    "uncertainty_frontier": "3. Scientific Uncertainty Frontier (High Model Disagreement & Entropy)",
    "hard_to_detect": "4. Hard-to-Detect Opportunity (Cryptic Species Recommending 15-20 Min Surveys)",
    "range_edge_surprise": "5. Exploratory Habitat-Analog Search (Provisional Range Surface)"
}

# Species detectability metadata catalog
SPECIES_DETECTABILITY_CATALOG = {
    "Passerina cyanea": {"detectability_class": "medium", "recommended_duration": 15, "cryptic_multiplier": 1.5},
    "Setophaga coronata": {"detectability_class": "low", "recommended_duration": 20, "cryptic_multiplier": 2.0},
    "Cardinalis cardinalis": {"detectability_class": "high", "recommended_duration": 5, "cryptic_multiplier": 1.0}
}

@dataclass(frozen=True)
class SpeciesOpportunityCell:
    """
    Structured Opportunity Cell Record powering map visual layers, route optimization,
    and location explanation cards. Tracks multi-dimensional provenance and result status.
    """
    species_id: str
    taxon_id: str
    site_id: int
    site_name: str
    week: int
    expected_presence: float
    expected_encounter: float
    epistemic_uncertainty: float
    checklist_effort: float
    habitat_similarity: float
    model_disagreement: float
    opportunity_score: float
    search_mode: str
    explanation: str
    evidence_provenance: str = "synthetic"      # "live_api", "curated_demo", "ebd_complete", "synthetic"
    prediction_provenance: str = "provisional_prior"  # "empirical_model", "provisional_prior", "simulated"
    result_status: str = "SIMULATED_DEMO"
    is_simulation_only: bool = True

def get_site_cell_id(site: Any) -> str:
    """Safely map CandidateSite to cell identifier."""
    cell_id = getattr(site, "cell_id", None)
    if cell_id is not None:
        return str(cell_id)
    return f"cell_{site.site_id}"

def calculate_opportunity_surface(
    dataset: Any,
    species_id: str,
    survey_week: int = 18,
    mode: str = "expected_undocumented",
    observer_profile: str = "Intermediate",
    species_evidence: Optional[List[SpeciesEvidence]] = None
) -> List[SpeciesOpportunityCell]:
    """
    Generate ranked SpeciesOpportunityCell surface across candidate sites for 1 of 5 search modes.
    Decouples ecological presence psi from conditional detectability p_detect|present.
    Uses canonical TaxonRef matching, species-specific QBC disagreement, evidence deduplication, and candidate cell mapping.
    """
    taxon = get_canonical_taxon(species_id)
    target_sp_id = taxon.common_name
    target_taxon_id = taxon.taxon_id

    phen = get_species_phenology(target_sp_id)
    weekly_abundance = phen.weekly_abundance[min(51, max(0, survey_week - 1))]

    # 1. Fit HabitatAnalogSearch using presence records (including presence_only and photo_verified)
    analog_engine = HabitatAnalogSearch()
    
    occurrence_records = []
    has_live_evidence = False
    has_curated_demo = False

    if species_evidence:
        for r in species_evidence:
            rec_taxon_id = getattr(r, "taxon_id", get_canonical_taxon(r.species_id).taxon_id)
            if rec_taxon_id == target_taxon_id:
                if "live" in r.source.lower() or "gbif" in r.source.lower() or "inaturalist" in r.source.lower():
                    has_live_evidence = True
                elif "curated" in r.source.lower() or "demo" in r.source.lower():
                    has_curated_demo = True

                is_presence = (
                    r.evidence_type in {"presence_only", "photo_verified_presence"}
                    or (r.evidence_type == "complete_checklist_detection" and r.detection is True)
                )
                if is_presence:
                    occurrence_records.append({
                        "lat": r.lat, "lon": r.lon, "cell_id": r.cell_id, "evidence_type": r.evidence_type
                    })

    if not occurrence_records:
        occurrence_records = [{"habitat": s.habitat} for s in dataset.candidate_sites[:5]]

    analog_engine.fit(
        target_sp_id, occurrence_records, background_candidates=dataset.candidate_sites
    )
    analog_matches = analog_engine.predict_habitat_match(dataset.candidate_sites)

    meta = SPECIES_DETECTABILITY_CATALOG.get(target_sp_id, SPECIES_DETECTABILITY_CATALOG.get(taxon.scientific_name, {"detectability_class": "medium", "recommended_duration": 10, "cryptic_multiplier": 1.2}))
    profile_multiplier = {"Beginner": 0.70, "Intermediate": 1.0, "Advanced": 1.30}.get(observer_profile, 1.0)
    cryptic_value = float(meta["cryptic_multiplier"])

    species_names = getattr(dataset, "species_names", [])
    target_sp_idx = species_names.index(target_sp_id) if target_sp_id in species_names else 0

    # Determine multi-dimensional provenance
    if has_live_evidence:
        ev_provenance = "live_api"
        res_status = "PROVISIONAL_MODEL_WITH_LIVE_OCCURRENCES"
        sim_only = False
    elif has_curated_demo:
        ev_provenance = "curated_demo"
        res_status = "CURATED_DEMO_ONLY"
        sim_only = True
    else:
        ev_provenance = "synthetic"
        res_status = "SIMULATED_DEMO"
        sim_only = True

    cells = []
    for idx, s in enumerate(dataset.candidate_sites):
        park_name = getattr(s, "park_name", f"Site {s.site_id}")
        cell_key = get_site_cell_id(s)
        covs = getattr(s, "env_covariates", None)
        canopy = covs.tree_canopy_pct if covs else s.habitat[0]

        # 1. Ecological Presence psi(s, i, t) in [0, 1]
        psi = float(np.clip(weekly_abundance * analog_matches[idx] * (1.2 if canopy > 0.3 else 0.8), 0.01, 0.99))

        # 2. Conditional Detectability given presence
        dur = float(getattr(s, "allocated_observation_minutes", getattr(s, "observation_minutes", 10)))
        p_detect_given_present = float(1.0 - math.exp(-0.08 * dur * profile_multiplier))

        # Relative Encounter Opportunity Index P(encounter) = psi * p_detect_given_present
        p_encounter = float(psi * p_detect_given_present)

        # 3. Model Disagreement & Epistemic Uncertainty from species-specific QBC or Bootstrap Matrix
        qbc_scores = getattr(s, "qbc_scores", None)
        if qbc_scores is not None and len(qbc_scores) > 0:
            if target_sp_idx < len(qbc_scores):
                qbc_disagreement = float(qbc_scores[target_sp_idx])
            else:
                qbc_disagreement = float(np.mean(qbc_scores))
        else:
            bootstrap = getattr(s, "bootstrap_predictions", None)
            if bootstrap is not None and getattr(bootstrap, "size", 0) > 0:
                qbc_arr = calculate_qbc_disagreement(bootstrap)
                if target_sp_idx < len(qbc_arr):
                    qbc_disagreement = float(qbc_arr[target_sp_idx])
                else:
                    qbc_disagreement = float(np.mean(qbc_arr))
            else:
                qbc_disagreement = 0.35

        entropy = float(-psi * math.log2(psi) - (1.0 - psi) * math.log2(1.0 - psi))

        # 4. Evidence Aggregation & Checklist Effort Coverage C(s, i, t)
        if species_evidence:
            ev_agg = aggregate_species_evidence(species_evidence, cell_id=cell_key, species_id=target_sp_id, target_week=survey_week)
            n_checklists = ev_agg["n_checklists"]
            coverage_C = ev_agg["coverage_score"]
        else:
            n_checklists = getattr(s, "n_checklists", 0)
            coverage_C = float(1.0 - math.exp(-0.35 * n_checklists))

        # 5. Compute Mode-Specific Opportunity Score
        if mode == "likely_encounter":
            score = p_encounter
            expl = f"High expected encounter index ({p_encounter*100:.1f}%) during Week {survey_week}."
        elif mode == "expected_undocumented":
            score = psi * (1.0 - coverage_C)
            expl = f"High habitat match ({analog_matches[idx]*100:.0f}%) with {n_checklists} prior complete checklists."
        elif mode == "uncertainty_frontier":
            score = entropy * qbc_disagreement * (1.0 - coverage_C)
            expl = f"High model disagreement ({qbc_disagreement:.3f}) and entropy ({entropy:.3f})."
        elif mode == "hard_to_detect":
            score = psi * (1.0 - p_detect_given_present) * cryptic_value
            expl = f"Cryptic target ({meta['detectability_class']}), recommending {meta['recommended_duration']} min stationary counts."
        elif mode == "range_edge_surprise":
            range_edge = float(getattr(s, "range_edge_index", 0.65))
            score = qbc_disagreement * range_edge * analog_matches[idx]
            expl = f"Exploratory habitat-analog site with range surface score ({range_edge:.2f})."
        else:
            score = psi * (1.0 - coverage_C)
            expl = f"Expected undocumented opportunity score: {score:.4f}."

        if sim_only and mode in {"expected_undocumented", "uncertainty_frontier", "range_edge_surprise"}:
            expl += " [Simulation Scaffold]"

        cells.append(SpeciesOpportunityCell(
            species_id=target_sp_id,
            taxon_id=target_taxon_id,
            site_id=s.site_id,
            site_name=park_name,
            week=survey_week,
            expected_presence=psi,
            expected_encounter=p_encounter,
            epistemic_uncertainty=entropy,
            checklist_effort=coverage_C,
            habitat_similarity=analog_matches[idx],
            model_disagreement=qbc_disagreement,
            opportunity_score=float(score),
            search_mode=mode,
            explanation=expl,
            evidence_provenance=ev_provenance,
            prediction_provenance="provisional_prior",
            result_status=res_status,
            is_simulation_only=sim_only
        ))

    return sorted(cells, key=lambda c: c.opportunity_score, reverse=True)
