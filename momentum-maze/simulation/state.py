import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PendulumState:
    theta: float  # Unwrapped angle in radians
    omega: float  # Angular velocity in rad/s


@dataclass(frozen=True)
class PendulumParameters:
    damping: float = 0.06
    torque_limit: float = 0.35
    gravity_over_length: float = 1.0


def wrap_theta(theta: float) -> float:
    """
    Wraps an unwrapped angle in radians into the range [-π, π).
    """
    wrapped = (theta + math.pi) % (2.0 * math.pi) - math.pi
    return wrapped


def energy(state: PendulumState) -> float:
    """
    Computes total energy E = 0.5 * ω² + 1 - cos(θ).
    Downward equilibrium (0, 0) has E = 0.
    Upright equilibrium (π, 0) / separatrix has E = 2.0.
    """
    return 0.5 * (state.omega**2) + (1.0 - math.cos(state.theta))
