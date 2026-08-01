from .state import PendulumState, PendulumParameters
from .pendulum import derivative


def rk4_step(
    state: PendulumState,
    torque: float,
    params: PendulumParameters,
    dt: float,
) -> PendulumState:
    """
    Advances state by dt using 4th-order Runge-Kutta integration.
    """
    k1 = derivative(state, torque, params)

    s_k2 = PendulumState(
        theta=state.theta + 0.5 * dt * k1.theta,
        omega=state.omega + 0.5 * dt * k1.omega,
    )
    k2 = derivative(s_k2, torque, params)

    s_k3 = PendulumState(
        theta=state.theta + 0.5 * dt * k2.theta,
        omega=state.omega + 0.5 * dt * k2.omega,
    )
    k3 = derivative(s_k3, torque, params)

    s_k4 = PendulumState(
        theta=state.theta + dt * k3.theta,
        omega=state.omega + dt * k3.omega,
    )
    k4 = derivative(s_k4, torque, params)

    new_theta = state.theta + (dt / 6.0) * (k1.theta + 2.0 * k2.theta + 2.0 * k3.theta + k4.theta)
    new_omega = state.omega + (dt / 6.0) * (k1.omega + 2.0 * k2.omega + 2.0 * k3.omega + k4.omega)

    return PendulumState(theta=new_theta, omega=new_omega)
