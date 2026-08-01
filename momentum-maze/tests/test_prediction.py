import pytest
from simulation.state import PendulumState, PendulumParameters
from simulation.integrator import rk4_step
from simulation.predictor import predict_trajectory


def test_prediction_matches_execution():
    """
    Guarantees that predicted trajectory matches committed gameplay execution step-for-step.
    """
    start_state = PendulumState(theta=0.5, omega=1.0)
    params = PendulumParameters(damping=0.06, torque_limit=0.35)
    torque = 0.35
    dt = 1.0 / 240.0
    pulse_dur = 0.35
    tail_dur = 1.05

    # 1. Run predictor
    predicted_states = predict_trajectory(
        start_state=start_state,
        torque=torque,
        params=params,
        pulse_duration=pulse_dur,
        tail_duration=tail_dur,
        dt=dt,
    )

    # 2. Simulate step-by-step manually
    manual_states = [start_state]
    curr = start_state
    pulse_steps = int(round(pulse_dur / dt))
    tail_steps = int(round(tail_dur / dt))

    for _ in range(pulse_steps):
        curr = rk4_step(curr, torque, params, dt)
        manual_states.append(curr)

    for _ in range(tail_steps):
        curr = rk4_step(curr, 0.0, params, dt)
        manual_states.append(curr)

    assert len(predicted_states) == len(manual_states)

    for p_st, m_st in zip(predicted_states, manual_states):
        assert pytest.approx(p_st.theta, abs=1e-12) == m_st.theta
        assert pytest.approx(p_st.omega, abs=1e-12) == m_st.omega
