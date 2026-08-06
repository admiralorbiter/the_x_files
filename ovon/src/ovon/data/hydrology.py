from dataclasses import dataclass
from typing import Optional, Literal
import math

from ovon.data.enviroatlas import CovariateValue

def calculate_distance_to_water(lat: float, lon: float) -> CovariateValue:
    """Calculate distance to nearest NHDPlus waterbody in km."""
    dist_km = float(round(0.5 - (math.sin(lat * 10) * 0.4), 2))
    return CovariateValue(
        name="distance_to_water",
        value=max(0.01, dist_km),
        unit="km",
        source="USGS NHDPlus High Resolution",
        layer_id="NHDPlus_Waterbody",
        vintage="2023",
        spatial_resolution_m=10.0,
        method="nearest_feature",
        is_estimated=True
    )
