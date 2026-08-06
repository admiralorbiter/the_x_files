import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

@dataclass
class SpeciesPhenologyProfile:
    common_name: str
    scientific_name: str
    migratory_status: str  # "Neotropical Migrant", "Winter Resident", "Year-Round Resident", "Summer Resident"
    peak_weeks: List[int]
    weekly_abundance: np.ndarray  # shape (52,) normalized in [0.0, 1.0]

def _gaussian_phenology_curve(peak_week: float, width_weeks: float = 3.0) -> np.ndarray:
    """Generate a smooth Gaussian annual abundance curve over 52 weeks."""
    weeks = np.arange(1, 53)
    d = np.minimum(np.abs(weeks - peak_week), 52 - np.abs(weeks - peak_week))
    return np.exp(-(d**2) / (2.0 * width_weeks**2))

def _bimodal_phenology_curve(peak1: float, peak2: float, width: float = 3.0) -> np.ndarray:
    """Generate a bimodal phenology curve (e.g. spring + fall migration peaks)."""
    c1 = _gaussian_phenology_curve(peak1, width)
    c2 = _gaussian_phenology_curve(peak2, width)
    curve = c1 + c2
    return curve / np.max(curve)

# Kansas City Provisional Phenology Priors
KC_PROVISIONAL_PHENOLOGY_PRIORS: Dict[str, SpeciesPhenologyProfile] = {
    "Indigo Bunting": SpeciesPhenologyProfile(
        common_name="Indigo Bunting",
        scientific_name="Passerina cyanea",
        migratory_status="Neotropical Summer Resident",
        peak_weeks=[20, 21, 22, 23, 24, 25, 26, 27, 28],
        weekly_abundance=_gaussian_phenology_curve(24.0, width_weeks=5.0)
    ),
    "Yellow-rumped Warbler": SpeciesPhenologyProfile(
        common_name="Yellow-rumped Warbler",
        scientific_name="Setophaga coronata",
        migratory_status="Spring & Fall Transient Migrant",
        peak_weeks=[17, 18, 19, 41, 42, 43],
        weekly_abundance=_bimodal_phenology_curve(18.0, 42.0, width=2.5)
    ),
    "Dark-eyed Junco": SpeciesPhenologyProfile(
        common_name="Dark-eyed Junco",
        scientific_name="Junco hyemalis",
        migratory_status="Winter Resident",
        peak_weeks=[1, 2, 3, 4, 5, 48, 49, 50, 51, 52],
        weekly_abundance=_gaussian_phenology_curve(52.0, width_weeks=8.0)
    ),
    "Gray Catbird": SpeciesPhenologyProfile(
        common_name="Gray Catbird",
        scientific_name="Dumetella carolinensis",
        migratory_status="Summer Breeding Resident",
        peak_weeks=[19, 20, 21, 22, 23, 24, 25, 26],
        weekly_abundance=_gaussian_phenology_curve(22.0, width_weeks=4.5)
    ),
    "House Finch": SpeciesPhenologyProfile(
        common_name="House Finch",
        scientific_name="Haemorhous mexicanus",
        migratory_status="Year-Round Resident",
        peak_weeks=list(range(1, 53)),
        weekly_abundance=np.full(52, 0.85)
    ),
    "Hooded Merganser": SpeciesPhenologyProfile(
        common_name="Hooded Merganser",
        scientific_name="Lophodytes cucullatus",
        migratory_status="Winter & Early Spring Waterbird",
        peak_weeks=[4, 5, 6, 7, 8, 46, 47, 48],
        weekly_abundance=_bimodal_phenology_curve(6.0, 47.0, width=3.5)
    ),
    "Chimney Swift": SpeciesPhenologyProfile(
        common_name="Chimney Swift",
        scientific_name="Chaetura pelagica",
        migratory_status="Summer Aerial Insectivore",
        peak_weeks=[20, 21, 22, 23, 24, 25, 26, 27],
        weekly_abundance=_gaussian_phenology_curve(23.0, width_weeks=4.0)
    ),
    "Peregrine Falcon": SpeciesPhenologyProfile(
        common_name="Peregrine Falcon",
        scientific_name="Falco peregrinus",
        migratory_status="Year-Round / Urban Cliff Resident",
        peak_weeks=list(range(1, 53)),
        weekly_abundance=np.full(52, 0.50)
    )
}

# Legacy alias
KC_SPECIES_PHENOLOGY_DATABASE = KC_PROVISIONAL_PHENOLOGY_PRIORS

def get_species_phenology(species_name: str) -> SpeciesPhenologyProfile:
    """Lookup 52-week phenology profile by common or scientific name with fallback."""
    for name, profile in KC_PROVISIONAL_PHENOLOGY_PRIORS.items():
        if species_name.lower() in name.lower() or species_name.lower() in profile.scientific_name.lower():
            return profile

    return SpeciesPhenologyProfile(
        common_name=species_name,
        scientific_name=species_name,
        migratory_status="Seasonal Migrant",
        peak_weeks=[18, 19, 20, 21, 22],
        weekly_abundance=_gaussian_phenology_curve(20.0, width_weeks=5.0)
    )

def fit_empirical_cyclic_phenology(
    weekly_detections: np.ndarray,
    weekly_checklists: np.ndarray
) -> np.ndarray:
    """
    Derive empirical phenology curve from complete eBird checklists using cyclic proportion smoothing:
    p_hat_{s,w} = detections / checklists.
    """
    raw_p = np.where(weekly_checklists > 0, weekly_detections / weekly_checklists, 0.0)
    # Apply 3-week cyclic moving average kernel smoothing
    kernel = np.array([0.25, 0.5, 0.25])
    padded = np.concatenate([raw_p[-1:], raw_p, raw_p[:1]])
    smoothed = np.convolve(padded, kernel, mode="valid")
    max_val = np.max(smoothed)
    return smoothed / max_val if max_val > 0 else smoothed

def get_weekly_species_weights(species_names: List[str], week: int) -> np.ndarray:
    """
    Compute dynamic, time-varying species optimization weights w_{s,t} for a target week t in [1, 52].
    """
    week_idx = int(np.clip(week - 1, 0, 51))
    weights = np.zeros(len(species_names), dtype=float)

    for i, sp in enumerate(species_names):
        prof = get_species_phenology(sp)
        abundance_t = float(prof.weekly_abundance[week_idx])
        
        if "Neotropical" in prof.migratory_status or "Transient" in prof.migratory_status:
            multiplier = 3.0
        elif "Winter" in prof.migratory_status:
            multiplier = 2.0
        else:
            multiplier = 1.0

        weights[i] = abundance_t * multiplier

    sum_w = float(np.sum(weights))
    if sum_w > 0:
        return weights / sum_w
    return np.ones(len(species_names)) / len(species_names)
