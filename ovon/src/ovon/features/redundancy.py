import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

from ovon.features.grid import EqualAreaGrid, GridCell
from ovon.utility.metrics import spatial_habitat_kernel

@dataclass
class CellWeekMetric:
    cell_id: int
    week: int
    n_checklists: int
    n_observers: int
    effective_coverage: float
    redundancy_index: float

class RedundancyAtlas:
    """
    Computes checklist counts, observer density, effective spatiotemporal coverage,
    and redundancy indices across spatial cells and weeks.
    """

    def __init__(self, grid: EqualAreaGrid):
        self.grid = grid
        self.cell_week_records: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

    def ingest_observations(self, observations: List[Dict[str, Any]]):
        """
        Ingest observation events.
        Each observation dict has: {'lat': float, 'lon': float, 'week': int, 'observer_id': str, 'habitat': np.ndarray}
        """
        for obs in observations:
            lat = obs["lat"]
            lon = obs["lon"]
            week = obs.get("week", 18)
            cell_id = self.grid.assign_point(lat, lon)

            if cell_id is not None:
                key = (cell_id, week)
                if key not in self.cell_week_records:
                    self.cell_week_records[key] = []
                self.cell_week_records[key].append(obs)

    def calculate_cell_week_metrics(
        self,
        week: int,
        length_spatial: float = 10.0,
        length_habitat: float = 0.5
    ) -> List[CellWeekMetric]:
        """
        Calculate CellWeekMetric for all cells in the grid for a specified week.
        """
        all_cells = self.grid.get_all_cells()
        metrics: List[CellWeekMetric] = []

        # Pre-collect all observations in target week
        week_obs = []
        for (cid, w), recs in self.cell_week_records.items():
            if w == week:
                cell = self.grid.get_cell(cid)
                for r in recs:
                    week_obs.append({
                        "x": cell.center_lat,
                        "y": cell.center_lon,
                        "habitat": r.get("habitat", np.array([0.33, 0.33, 0.34]))
                    })

        for cell in all_cells:
            key = (cell.cell_id, week)
            recs = self.cell_week_records.get(key, [])

            n_checklists = len(recs)
            n_observers = len(set(r.get("observer_id", "obs_0") for r in recs))

            # Effective spatiotemporal coverage
            cell_hab = np.array([0.33, 0.33, 0.34])
            coverage = 0.0
            for o in week_obs:
                k = spatial_habitat_kernel(
                    cell.center_lat, cell.center_lon, cell_hab,
                    o["x"], o["y"], o["habitat"],
                    length_spatial=length_spatial,
                    length_habitat=length_habitat
                )
                coverage += k

            redundancy = float(coverage / (1.0 + coverage))

            metrics.append(CellWeekMetric(
                cell_id=cell.cell_id,
                week=week,
                n_checklists=n_checklists,
                n_observers=n_observers,
                effective_coverage=float(coverage),
                redundancy_index=redundancy
            ))

        return metrics

    def get_top_undersampled_cells(self, week: int, top_k: int = 10) -> List[Tuple[GridCell, CellWeekMetric]]:
        """Return the top_k most under-sampled grid cells for a given week."""
        metrics = self.calculate_cell_week_metrics(week)
        sorted_metrics = sorted(metrics, key=lambda m: m.effective_coverage)
        
        result = []
        for m in sorted_metrics[:top_k]:
            cell = self.grid.get_cell(m.cell_id)
            result.append((cell, m))
        return result
