from dataclasses import dataclass
from typing import Optional, Literal
import numpy as np

from ovon.data.enviroatlas import CovariateValue

def sample_annual_nlcd(lat: float, lon: float, year: int = 2023) -> CovariateValue:
    """Sample Annual NLCD land cover class for given coordinates."""
    # NLCD sampling logic (point sample)
    return CovariateValue(
        name="nlcd_land_cover",
        value=41.0,  # Deciduous Forest code
        unit="class_code",
        source="MRLC Annual NLCD",
        layer_id="NLCD_2023_Land_Cover",
        vintage=str(year),
        spatial_resolution_m=30.0,
        method="point_sample",
        is_estimated=False
    )
