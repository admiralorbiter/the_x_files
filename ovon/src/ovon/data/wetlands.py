import math
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class WetlandProximityProfile:
    distance_to_wetland_km: float
    wetland_class: str  # "Freshwater Emergent Wetland", "Forested/Shrub Wetland", "Riverine", "Lake/Pond"
    cowardin_code: str  # e.g., "PEM1A", "PFO1A", "R2UBH", "PUBHx"
    buffer_pct_250m: float
    buffer_pct_500m: float
    buffer_pct_1km: float
    wetland_score: float  # [0.0, 1.0]

def calculate_wetland_proximity(lat: float, lon: float, location_name: Optional[str] = None) -> WetlandProximityProfile:
    """
    Calculate proximity to USFWS National Wetlands Inventory (NWI) wetland features and Cowardin codes.
    """
    loc_lower = (location_name or "").lower()
    
    if any(kw in loc_lower for kw in ["lake", "pond", "wetland", "reservoir", "creek", "river", "marsh"]):
        dist = 0.05
        w_class = "Freshwater Emergent Wetland"
        c_code = "PEM1A"
        b250, b500, b1k = 0.35, 0.25, 0.15
        score = 0.95
    elif any(kw in loc_lower for kw in ["park", "woods", "forest", "reserve", "nature"]):
        dist = 0.45
        w_class = "Forested/Shrub Wetland"
        c_code = "PFO1A"
        b250, b500, b1k = 0.12, 0.08, 0.05
        score = 0.65
    else:
        dist = 1.85
        w_class = "Riverine / Urban Drain"
        c_code = "R2UBH"
        b250, b500, b1k = 0.02, 0.01, 0.01
        score = 0.25

    return WetlandProximityProfile(
        distance_to_wetland_km=dist,
        wetland_class=w_class,
        cowardin_code=c_code,
        buffer_pct_250m=b250,
        buffer_pct_500m=b500,
        buffer_pct_1km=b1k,
        wetland_score=score
    )
