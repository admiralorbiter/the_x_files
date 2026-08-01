import math
import pytest
from simulation.state import PendulumState, energy


def test_downward_equilibrium_energy():
    state = PendulumState(theta=0.0, omega=0.0)
    assert pytest.approx(energy(state), abs=1e-6) == 0.0


def test_upright_equilibrium_energy():
    state = PendulumState(theta=math.pi, omega=0.0)
    assert pytest.approx(energy(state), abs=1e-6) == 2.0


def test_pure_kinetic_energy():
    state = PendulumState(theta=0.0, omega=2.0)
    # E = 0.5 * 2^2 + 1 - cos(0) = 2.0
    assert pytest.approx(energy(state), abs=1e-6) == 2.0


def test_separatrix_energy():
    # At theta = pi/2, for E = 2.0: 0.5*omega^2 + 1 - 0 = 2.0 => omega = sqrt(2)
    state = PendulumState(theta=math.pi / 2.0, omega=math.sqrt(2.0))
    assert pytest.approx(energy(state), abs=1e-6) == 2.0
