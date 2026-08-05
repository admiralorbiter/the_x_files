import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
import yaml

@dataclass
class ProjectConfig:
    name: str = "ovon"
    pilot_region: str = "Greater Kansas City"
    center_lat: float = 39.0997
    center_lon: float = -94.5786
    radius_km: float = 100.0
    grid_resolution_km: float = 3.0
    route_budgets_minutes: List[int] = field(default_factory=lambda: [45, 90, 180])
    stops_per_route: List[int] = field(default_factory=lambda: [3, 5])
    minutes_per_stop: int = 10
    bootstrap_models: int = 30
    synthetic_n_cells: int = 100
    synthetic_n_sites: int = 40
    synthetic_n_species: int = 8
    random_seed: int = 42

    @classmethod
    def load_from_yaml(cls, path: str) -> "ProjectConfig":
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        proj = data.get("project", {})
        grid = data.get("grid", {})
        proto = data.get("field_protocol", {})
        model = data.get("model", {})
        synth = data.get("synthetic", {})

        return cls(
            name=proj.get("name", "ovon"),
            pilot_region=proj.get("pilot_region", "Greater Kansas City"),
            center_lat=proj.get("center", {}).get("latitude", 39.0997),
            center_lon=proj.get("center", {}).get("longitude", -94.5786),
            radius_km=proj.get("radius_km", 100.0),
            grid_resolution_km=grid.get("resolution_km", 3.0),
            route_budgets_minutes=proto.get("route_budgets_minutes", [45, 90, 180]),
            stops_per_route=proto.get("stops_per_route", [3, 5]),
            minutes_per_stop=proto.get("minutes_per_stop", 10),
            bootstrap_models=model.get("bootstrap_models", 30),
            synthetic_n_cells=synth.get("n_cells", 100),
            synthetic_n_sites=synth.get("n_candidate_sites", 40),
            synthetic_n_species=synth.get("n_species", 8),
            random_seed=synth.get("random_seed", 42),
        )
