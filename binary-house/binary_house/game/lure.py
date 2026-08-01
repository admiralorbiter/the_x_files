from dataclasses import dataclass
from binary_house.core.ball import Ball

@dataclass
class LureRegion:
    """A decoy lineage lure dropped by the player that attracts the Caretaker."""
    ball: Ball
    turns_remaining: int = 3

    def tick(self) -> bool:
        """Advance turn timer. Returns True while lure is still active."""
        self.turns_remaining -= 1
        return self.turns_remaining > 0
