import json
from dataclasses import asdict, dataclass, field
from typing import List, Dict, Any
from simulation.state import PendulumState


@dataclass
class PulseRecord:
    torque: float
    committed_at: float


@dataclass
class ReplayRecorder:
    level_id: str = "chamber_00"
    initial_theta: float = 0.0
    initial_omega: float = 0.0
    pulses: List[PulseRecord] = field(default_factory=list)

    def record_pulse(self, torque: float, sim_time: float):
        self.pulses.append(PulseRecord(torque=torque, committed_at=sim_time))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_id": self.level_id,
            "initial_theta": self.initial_theta,
            "initial_omega": self.initial_omega,
            "pulses": [asdict(p) for p in self.pulses],
        }

    def save_to_file(self, filepath: str):
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ReplayRecorder":
        with open(filepath, "r") as f:
            data = json.load(f)

        pulses = [
            PulseRecord(torque=p["torque"], committed_at=p["committed_at"])
            for p in data.get("pulses", [])
        ]

        return cls(
            level_id=data["level_id"],
            initial_theta=data["initial_theta"],
            initial_omega=data["initial_omega"],
            pulses=pulses,
        )
