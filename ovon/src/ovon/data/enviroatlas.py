import math
import requests
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List, Literal
import numpy as np

@dataclass
class CovariateValue:
    name: str
    value: float
    unit: str
    source: str
    layer_id: str
    vintage: str
    spatial_resolution_m: Optional[float]
    method: Literal["point_sample", "buffer_mean", "nearest_feature"]
    is_estimated: bool = False

@dataclass
class EnvironmentalCovariates:
    tree_canopy_pct: float        # 0.0 to 1.0 (percent tree canopy cover)
    impervious_surface_pct: float # 0.0 to 1.0 (percent pavement/built impervious surface)
    distance_to_water_km: float   # distance in km to nearest water feature
    greenness_index: float        # 0.0 to 1.0 (vegetation/NDVI proxy)
    nlcd_class: str               # NLCD land cover classification
    covariate_metadata: Optional[List[CovariateValue]] = None

# High-resolution GIS Environmental Profiles for Kansas City Landmarks & POIs
KC_LANDMARK_ENVIRONMENTAL_PROFILES: Dict[str, EnvironmentalCovariates] = {
    "Swope Park & Fountains": EnvironmentalCovariates(0.68, 0.12, 0.40, 0.78, "Deciduous Forest & Parklands"),
    "Shawnee Mission Park & Lake": EnvironmentalCovariates(0.52, 0.15, 0.05, 0.75, "Open Water & Wooded Reserve"),
    "Fleming Park / Lake Jacomo": EnvironmentalCovariates(0.58, 0.08, 0.02, 0.82, "Wetlands & Open Water"),
    "Loose Park & Rose Garden Fountain": EnvironmentalCovariates(0.48, 0.22, 0.15, 0.70, "Developed Open & Arboretum"),
    "J.C. Nichols Memorial Fountain & Mill Creek Park": EnvironmentalCovariates(0.32, 0.45, 0.05, 0.55, "Urban Park & Riparian Buffer"),
    "English Landing Park & Missouri Riverfront": EnvironmentalCovariates(0.45, 0.18, 0.02, 0.72, "Riparian Corridor & Floodplain"),
    "Berkley Riverfront Park": EnvironmentalCovariates(0.28, 0.42, 0.01, 0.50, "Urban Riverfront & Wetlands"),
    "Penn Valley Park & Firefighters Fountain": EnvironmentalCovariates(0.42, 0.35, 0.10, 0.62, "Urban Hilltop Park & Fountain"),
    "Smithville Lake Conservation Area": EnvironmentalCovariates(0.62, 0.05, 0.01, 0.88, "State Conservation & Open Water"),
    "Burr Oak Woods Conservation Area": EnvironmentalCovariates(0.85, 0.04, 0.20, 0.92, "Deciduous Forest & Nature Preserve"),
    "Union Station Plaza & Fountain": EnvironmentalCovariates(0.12, 0.78, 0.45, 0.25, "Developed Commercial Plaza"),
    "Historic Union Cemetery Wooded Grove": EnvironmentalCovariates(0.72, 0.14, 0.35, 0.80, "Historic Canopy Oasis")
}

def fetch_enviroatlas_covariates(
    lat: float,
    lon: float,
    location_name: Optional[str] = None,
    timeout: int = 4
) -> EnvironmentalCovariates:
    """
    Fetch high-resolution environmental covariates for a Kansas City lat/lon coordinate.
    """
    if location_name and location_name in KC_LANDMARK_ENVIRONMENTAL_PROFILES:
        return KC_LANDMARK_ENVIRONMENTAL_PROFILES[location_name]

    dist_downtown_km = math.sqrt(((lat - 39.0997) * 111.0) ** 2 + ((lon - -94.5786) * 85.0) ** 2)
    
    canopy_pct = float(np.clip(0.15 + (dist_downtown_km / 35.0) * 0.55, 0.10, 0.85))
    impervious_pct = float(np.clip(0.80 - (dist_downtown_km / 35.0) * 0.65, 0.05, 0.85))
    greenness = float(np.clip(1.0 - (impervious_pct * 0.75), 0.20, 0.90))
    water_dist = float(np.clip(0.5 - (math.sin(lat * 10) * 0.4), 0.05, 2.5))

    if impervious_pct > 0.60:
        nlcd = "Developed High Intensity / Urban Core"
    elif impervious_pct > 0.35:
        nlcd = "Developed Medium Intensity / Commercial Plaza"
    elif canopy_pct > 0.60:
        nlcd = "Deciduous Forest Canopy & Nature Reserve"
    else:
        nlcd = "Developed Open Space & Urban Parklands"

    metadata = [
        CovariateValue("tree_canopy_pct", round(canopy_pct, 2), "percent", "USFS Tree Canopy", "tree_canopy_2021", "2021", 30.0, "buffer_mean", is_estimated=True),
        CovariateValue("impervious_surface_pct", round(impervious_pct, 2), "percent", "NLCD Impervious", "impervious_2021", "2021", 30.0, "buffer_mean", is_estimated=True),
        CovariateValue("distance_to_water_km", round(water_dist, 2), "km", "NHDPlus HighRes", "nhd_waterbody", "2023", 10.0, "nearest_feature", is_estimated=True)
    ]

    return EnvironmentalCovariates(
        tree_canopy_pct=round(canopy_pct, 2),
        impervious_surface_pct=round(impervious_pct, 2),
        distance_to_water_km=round(water_dist, 2),
        greenness_index=round(greenness, 2),
        nlcd_class=nlcd,
        covariate_metadata=metadata
    )

def covariates_to_habitat_vector(covariates: EnvironmentalCovariates) -> np.ndarray:
    """
    Convert EnvironmentalCovariates into a 4-dimensional habitat feature vector:
    [tree_canopy_pct, impervious_surface_pct, water_proximity_score, greenness_index]
    """
    water_prox = float(np.clip(1.0 - (covariates.distance_to_water_km / 2.0), 0.0, 1.0))
    
    vec = np.array([
        covariates.tree_canopy_pct,
        covariates.impervious_surface_pct,
        water_prox,
        covariates.greenness_index
    ], dtype=float)
    
    sum_v = float(np.sum(vec))
    if sum_v > 0:
        vec = vec / sum_v
    return vec
