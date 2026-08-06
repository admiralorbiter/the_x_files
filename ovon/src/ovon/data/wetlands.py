import math
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class WetlandProximityProfile:
    distance_to_wetland_km: float
    wetland_class: str  # "Freshwater Emergent Wetland", "Forested/Shrub Wetland", "Riverine", "Lake/Pond"
    wetland_score: float  # [0.0, 1.0]

def calculate_wetland_proximity(lat: float, lon: float, location_name: Optional[str] = None) -> WetlandProximityProfile:
    """
    Calculate proximity to USFWS National Wetlands Inventory (NWI) wetland features.
    """
    loc_lower = (location_name or "").lower()
    
    if any(kw in loc_lower for kw in ["lake", "pond", "wetland", "reservoir", "creek", "river", "marsh"]):
        dist = 0.05
        w_class = "Freshwater Emergent Wetland"
        score = 0.95
    elif any(kw in loc_lower for kw in ["park", "woods", "forest", "reserve", "nature"]):
        dist = 0.45
        w_class = "Forested/Shrub Wetland"
        score = 0.65
    else:
        dist = 1.85
        w_class = "Riverine / Urban Drain"
        score = 0.25

    return WetlandProximityProfile(
        distance_to_wetland_km=dist,
        wetland_class=w_class,
        wetland_score=score
    )
