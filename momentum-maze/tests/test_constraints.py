import math
import pytest
from simulation.state import PendulumState
from game.constraints import (
    StateGate,
    SpeedBarrier,
    DirectionalGate,
    EnergyLock,
    RotationKey,
    UprightDock,
    DownwardDock,
)


def test_state_gate_crossing():
    gate = StateGate(target_theta=1.0, omega_min=0.5, omega_max=1.5)

    s_prev = PendulumState(theta=0.9, omega=1.0)
    s_curr = PendulumState(theta=1.1, omega=1.0)

    res = gate.check_transition(s_prev, s_curr)
    assert res.satisfied is True
    assert res.failed is False


def test_state_gate_speed_mismatch():
    gate = StateGate(target_theta=1.0, omega_min=0.5, omega_max=1.5)

    s_prev = PendulumState(theta=0.9, omega=2.0)
    s_curr = PendulumState(theta=1.1, omega=2.0)

    res = gate.check_transition(s_prev, s_curr)
    assert res.failed is True


def test_speed_barrier_hazard():
    barrier = SpeedBarrier(max_omega=3.0)

    s_safe = PendulumState(theta=0.0, omega=2.5)
    res1 = barrier.check_transition(s_safe, s_safe)
    assert res1.failed is False

    s_unsafe = PendulumState(theta=0.0, omega=3.5)
    res2 = barrier.check_transition(s_safe, s_unsafe)
    assert res2.failed is True


def test_rotation_key():
    key = RotationKey(start_theta=0.0)

    s_init = PendulumState(theta=0.0, omega=1.0)
    s_mid = PendulumState(theta=math.pi, omega=1.0)
    s_rot = PendulumState(theta=2.1 * math.pi, omega=1.0)

    assert key.check_transition(s_init, s_mid).satisfied is False
    assert key.check_transition(s_mid, s_rot).satisfied is True


def test_upright_dock():
    dock = UprightDock(theta_tol=0.15, omega_tol=0.2)

    s_top = PendulumState(theta=math.pi, omega=0.05)
    res = dock.check_transition(s_top, s_top)
    assert res.satisfied is True
