import math
from .state import PendulumState, PendulumParameters


def derivative(
    state: PendulumState,
    torque: float,
    params: PendulumParameters,
) -> PendulumState:
    """
    Computes state derivative (dθ/dt, dω/dt) for the physical pendulum:
      dθ/dt = ω
      dω/dt = - (g/l) * sin(θ) - β * ω + u / (m*l^2)
    where torque u is clamped to [-u_max, u_max].
    """
    bounded_torque = max(-params.torque_limit, min(params.torque_limit, torque))

    d_theta = state.omega
    d_omega = (
        -params.gravity_over_length * math.sin(state.theta)
        - params.damping * state.omega
        + bounded_torque
    )

    return PendulumState(theta=d_theta, omega=d_omega)
