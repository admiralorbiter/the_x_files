from dataclasses import dataclass


@dataclass
class ScoreTracker:
    powered_pulses: int = 0
    total_pulses: int = 0
    control_effort: float = 0.0
    elapsed_time: float = 0.0

    def record_pulse(self, torque: float, pulse_duration: float = 0.35):
        self.total_pulses += 1
        if abs(torque) > 1e-4:
            self.powered_pulses += 1
        self.control_effort += abs(torque) * pulse_duration

    def add_time(self, dt: float):
        self.elapsed_time += dt

    def reset(self):
        self.powered_pulses = 0
        self.total_pulses = 0
        self.control_effort = 0.0
        self.elapsed_time = 0.0
