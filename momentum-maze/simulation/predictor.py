from typing import List
from .state import PendulumState, PendulumParameters
from .integrator import rk4_step


def predict_trajectory(
    start_state: PendulumState,
    torque: float,
    params: PendulumParameters,
    pulse_duration: float = 0.35,
    tail_duration: float = 1.05,
    dt: float = 1.0 / 240.0,
) -> List[PendulumState]:
    """
    Predicts trajectory points over pulse_duration (with torque) followed by
    tail_duration (with torque=0.0). Uses exact rk4_step simulation code.
    """
    trajectory: List[PendulumState] = [start_state]
    current = start_state

    pulse_steps = int(round(pulse_duration / dt))
    tail_steps = int(round(tail_duration / dt))

    # Phase 1: Applied pulse
    for _ in range(pulse_steps):
        current = rk4_step(current, torque, params, dt)
        trajectory.append(current)

    # Phase 2: Coasting (zero torque)
    for _ in range(tail_steps):
        current = rk4_step(current, 0.0, params, dt)
        trajectory.append(current)

    return trajectory
