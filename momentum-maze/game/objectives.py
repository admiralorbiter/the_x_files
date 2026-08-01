from typing import List, Optional, Any
from simulation.state import PendulumState
from .constraints import PhaseConstraint, ConstraintResult


class ObjectiveManager:
    def __init__(self, constraints: List[Any], target_description: str = "Dock"):
        self.constraints = constraints
        self.target_description = target_description
        self.active_index = 0

        self.is_completed = False
        self.is_failed = False
        self.status_message = "Chamber active"

    def check_step(
        self,
        previous: PendulumState,
        current: PendulumState,
        pulse_count: int,
        pulse_budget: Optional[int],
    ):
        """Evaluates constraints on physics step."""
        if self.is_completed or self.is_failed:
            return

        # Check pulse budget limit if set
        if pulse_budget is not None and pulse_count > pulse_budget:
            self.is_failed = True
            self.status_message = f"OUT OF PULSES! Used {pulse_count}/{pulse_budget}"
            return

        # Check all constraints for failure / satisfaction
        for i, constraint in enumerate(self.constraints):
            res: ConstraintResult = constraint.check_transition(previous, current)

            if res.failed:
                self.is_failed = True
                self.status_message = res.message
                return

            if res.satisfied:
                # Check if this is the active objective step
                if i == self.active_index:
                    self.active_index += 1
                    self.status_message = res.message

                    # All objectives satisfied?
                    if self.active_index >= len(self.constraints):
                        self.is_completed = True
                        self.status_message = "CHAMBER COMPLETED SUCCESSFULLY!"
                        return
