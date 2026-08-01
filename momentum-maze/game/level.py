import json
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from simulation.state import PendulumState, PendulumParameters
from .constraints import (
    StateGate,
    SpeedBarrier,
    DirectionalGate,
    EnergyLock,
    RotationKey,
    UprightDock,
    DownwardDock,
)
from .objectives import ObjectiveManager


@dataclass
class ChamberLevel:
    id: str
    name: str
    initial_state: PendulumState
    parameters: PendulumParameters
    pulse_budget: Optional[int]
    controls_enabled: bool
    constraints: List[Any]
    objective_manager: ObjectiveManager
    tutorial_flags: List[str]


def load_chamber(filepath_or_dict: Any) -> ChamberLevel:
    """Loads chamber from JSON file path or dictionary."""
    if isinstance(filepath_or_dict, str):
        with open(filepath_or_dict, "r") as f:
            data = json.load(f)
    else:
        data = filepath_or_dict

    level_id = data.get("id", "chamber_00")
    name = data.get("name", "Unnamed Chamber")

    init_st_dict = data.get("initial_state", {"theta": 0.0, "omega": 0.0})
    initial_state = PendulumState(
        theta=init_st_dict.get("theta", 0.0),
        omega=init_st_dict.get("omega", 0.0),
    )

    param_dict = data.get("parameters", {})
    params = PendulumParameters(
        damping=param_dict.get("damping", 0.06),
        torque_limit=param_dict.get("torque_limit", 0.35),
        gravity_over_length=param_dict.get("gravity_over_length", 1.0),
    )

    pulse_budget = data.get("pulse_budget", None)
    controls_enabled = data.get("controls_enabled", True)
    tutorial_flags = data.get("tutorial_flags", [])
    target_desc = data.get("target_description", "Dock")

    raw_constraints = data.get("constraints", [])
    constraints = []

    for c in raw_constraints:
        c_type = c.get("type")
        if c_type == "state_gate":
            constraints.append(
                StateGate(
                    target_theta=c["target_theta"],
                    omega_min=c["omega_min"],
                    omega_max=c["omega_max"],
                    name=c.get("name", "State Gate"),
                )
            )
        elif c_type == "speed_barrier":
            constraints.append(
                SpeedBarrier(
                    max_omega=c["max_omega"],
                    name=c.get("name", "Speed Barrier"),
                )
            )
        elif c_type == "directional_gate":
            constraints.append(
                DirectionalGate(
                    target_theta=c["target_theta"],
                    require_positive_omega=c.get("require_positive_omega", True),
                )
            )
        elif c_type == "energy_lock":
            constraints.append(
                EnergyLock(
                    min_energy=c["min_energy"],
                    max_energy=c["max_energy"],
                )
            )
        elif c_type == "rotation_key":
            constraints.append(
                RotationKey(
                    start_theta=initial_state.theta,
                    name=c.get("name", "Rotation Key"),
                )
            )
        elif c_type == "upright_dock":
            constraints.append(
                UprightDock(
                    theta_tol=c.get("theta_tol", 0.12),
                    omega_tol=c.get("omega_tol", 0.18),
                    name=c.get("name", "Upright Dock"),
                )
            )
        elif c_type == "downward_dock":
            constraints.append(
                DownwardDock(
                    theta_tol=c.get("theta_tol", 0.12),
                    omega_tol=c.get("omega_tol", 0.15),
                    name=c.get("name", "Downward Dock"),
                )
            )

    obj_mgr = ObjectiveManager(constraints=constraints, target_description=target_desc)

    return ChamberLevel(
        id=level_id,
        name=name,
        initial_state=initial_state,
        parameters=params,
        pulse_budget=pulse_budget,
        controls_enabled=controls_enabled,
        constraints=constraints,
        objective_manager=obj_mgr,
        tutorial_flags=tutorial_flags,
    )
