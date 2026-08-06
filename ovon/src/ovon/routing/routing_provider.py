from typing import Protocol, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class Coordinate:
    lat: float
    lon: float

@dataclass
class RouteGeometry:
    coordinates: List[Tuple[float, float]]
    distance_meters: float
    duration_seconds: float
    instructions: List[str]

class RoutingProvider(Protocol):
    def duration_matrix(
        self,
        coordinates: List[Coordinate],
        mode: str = "walking"
    ) -> np.ndarray:
        """Calculate travel duration matrix in minutes between all coordinates."""
        ...

    def route_geometry(
        self,
        ordered_coordinates: List[Coordinate],
        mode: str = "walking"
    ) -> RouteGeometry:
        """Calculate route geometry and travel duration along sequence of coordinates."""
        ...
