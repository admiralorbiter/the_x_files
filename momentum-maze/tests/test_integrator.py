import math
import pytest
from simulation.state import PendulumState, PendulumParameters, energy
from simulation.integrator import rk4_step


def test_equilibrium_fixed_point():
    state = PendulumState(theta=0.0, omega=0.0)
    params = PendulumParameters()
    dt = 1.0 / 240.0

    for _ in range(1000):
        state = rk4_step(state, torque=0.0, params=params, dt=dt)

    assert abs(state.theta) < 1e-6
    assert abs(state.omega) < 1e-6


def test_energy_conservation_undamped():
    params = PendulumParameters(damping=0.0)
    state = PendulumState(theta=1.0, omega=0.5)
    e0 = energy(state)
    dt = 1.0 / 240.0

    # Simulate 10 seconds of motion
    for _ in range(2400):
        state = rk4_step(state, torque=0.0, params=params, dt=dt)

    e_final = energy(state)
    assert abs(e_final - e0) < 1e-4


def test_damping_energy_decay():
    params = PendulumParameters(damping=0.06)
    state = PendulumState(theta=1.5, omega=1.0)
    e0 = energy(state)
    dt = 1.0 / 240.0

    for _ in range(480):  # 2 seconds
        state = rk4_step(state, torque=0.0, params=params, dt=dt)

    e_final = energy(state)
    assert e_final < e0


def test_control_adds_energy():
    params = PendulumParameters(damping=0.0, torque_limit=0.35)
    # Moving clockwise (omega > 0)
    state = PendulumState(theta=0.0, omega=1.0)
    dt = 1.0 / 240.0

    # Positive torque with positive omega
    state_pos = rk4_step(state, torque=0.35, params=params, dt=dt)
    state_neu = rk4_step(state, torque=0.0, params=params, dt=dt)

    assert energy(state_pos) > energy(state_neu)
