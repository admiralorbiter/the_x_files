import math
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional, Any
import numpy as np

@dataclass
class GridCell:
    cell_id: int
    row: int
    col: int
    center_lat: float
    center_lon: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    area_sq_km: float = 9.0  # 3 km x 3 km

class EqualAreaGrid:
    """
    Projected Equal-Area 3 km Square Grid centered on Kansas City (39.0997, -94.5786).
    """

    def __init__(
        self,
        center_lat: float = 39.0997,
        center_lon: float = -94.5786,
        radius_km: float = 50.0,
        resolution_km: float = 3.0
    ):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_km = radius_km
        self.resolution_km = resolution_km

        # Approximate degree scaling for Kansas City latitude (~39.1 deg N)
        self.km_per_lat_deg = 111.0
        self.km_per_lon_deg = 111.0 * math.cos(math.radians(center_lat))

        # Determine grid dimensions
        self.span_km = 2.0 * radius_km
        self.n_cols = int(math.ceil(self.span_km / resolution_km))
        self.n_rows = int(math.ceil(self.span_km / resolution_km))
        self.total_cells = self.n_rows * self.n_cols

        # Compute bounding box in degrees
        half_span_lat = (radius_km / self.km_per_lat_deg)
        half_span_lon = (radius_km / self.km_per_lon_deg)

        self.min_lat = center_lat - half_span_lat
        self.max_lat = center_lat + half_span_lat
        self.min_lon = center_lon - half_span_lon
        self.max_lon = center_lon + half_span_lon

        self.lat_step = (self.max_lat - self.min_lat) / self.n_rows
        self.lon_step = (self.max_lon - self.min_lon) / self.n_cols

    def assign_point(self, lat: float, lon: float) -> Optional[int]:
        """Map latitude and longitude to grid cell_id."""
        if lat < self.min_lat or lat > self.max_lat or lon < self.min_lon or lon > self.max_lon:
            return None

        row = int((lat - self.min_lat) / self.lat_step)
        col = int((lon - self.min_lon) / self.lon_step)

        row = min(row, self.n_rows - 1)
        col = min(col, self.n_cols - 1)

        return row * self.n_cols + col

    def get_cell(self, cell_id: int) -> GridCell:
        """Retrieve GridCell metadata by cell_id."""
        if cell_id < 0 or cell_id >= self.total_cells:
            raise ValueError(f"Invalid cell_id: {cell_id}. Must be 0 <= cell_id < {self.total_cells}")

        row = cell_id // self.n_cols
        col = cell_id % self.n_cols

        c_min_lat = self.min_lat + row * self.lat_step
        c_max_lat = c_min_lat + self.lat_step
        c_min_lon = self.min_lon + col * self.lon_step
        c_max_lon = c_min_lon + self.lon_step

        center_lat = (c_min_lat + c_max_lat) / 2.0
        center_lon = (c_min_lon + c_max_lon) / 2.0

        return GridCell(
            cell_id=cell_id,
            row=row,
            col=col,
            center_lat=center_lat,
            center_lon=center_lon,
            min_lat=c_min_lat,
            max_lat=c_max_lat,
            min_lon=c_min_lon,
            max_lon=c_max_lon,
            area_sq_km=self.resolution_km ** 2
        )

    def get_all_cells(self) -> List[GridCell]:
        """Return list of all GridCells in the grid."""
        return [self.get_cell(cid) for cid in range(self.total_cells)]

    def extract_multiscale_habitat_features(
        self,
        cell_id: int,
        buffers_m: Tuple[int, ...] = (500, 1500, 3000),
        seed: int = 42
    ) -> Dict[str, np.ndarray]:
        """
        Extract multiscale habitat composition features (forest, wetland, urban)
        at specified spatial buffer radii (e.g., 500m, 1500m, 3000m).
        """
        cell = self.get_cell(cell_id)
        # Deterministic habitat composition based on cell coordinates
        rng = np.random.default_rng(seed + cell_id)
        
        base_forest = 0.4 + 0.3 * math.sin(cell.center_lat * 10.0)
        base_wetland = 0.3 + 0.2 * math.cos(cell.center_lon * 10.0)
        base_urban = max(0.1, 1.0 - (base_forest + base_wetland))

        raw_vector = np.array([max(0.05, base_forest), max(0.05, base_wetland), max(0.05, base_urban)])
        base_comp = raw_vector / np.sum(raw_vector)

        features = {}
        for buf in buffers_m:
            noise = rng.normal(0, 0.05, size=3)
            buf_comp = np.clip(base_comp + noise, 0.01, 0.99)
            buf_comp /= np.sum(buf_comp)
            features[f"habitat_buffer_{buf}m"] = buf_comp

        return features
