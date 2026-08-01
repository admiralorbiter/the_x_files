import math
import pytest
from simulation.state import wrap_theta


def test_wrap_theta_in_range():
    assert pytest.approx(wrap_theta(0.5)) == 0.5
    assert pytest.approx(wrap_theta(-1.2)) == -1.2


def test_wrap_theta_overflow():
    assert pytest.approx(wrap_theta(math.pi + 0.1)) == pytest.approx(-math.pi + 0.1)
    assert pytest.approx(wrap_theta(-math.pi - 0.1)) == pytest.approx(math.pi - 0.1)


def test_wrap_theta_multiple_rotations():
    assert pytest.approx(wrap_theta(4.0 * math.pi + 0.5)) == pytest.approx(0.5)
    assert pytest.approx(wrap_theta(-6.0 * math.pi - 1.0)) == pytest.approx(-1.0)
