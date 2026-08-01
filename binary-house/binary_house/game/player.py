from dataclasses import dataclass
from typing import Protocol
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit, AffineDoor
from binary_house.core.ball import Ball

class PlayerAction(Protocol):
    def action_type(self) -> str:
        ...


@dataclass(frozen=True)
class MoveAction:
    door: ToggleDigit

    def action_type(self) -> str:
        return "move"


@dataclass(frozen=True)
class UseChalk:
    depth: int

    def action_type(self) -> str:
        return "chalk"


@dataclass(frozen=True)
class UseQuietSteps:
    door: ToggleDigit

    def action_type(self) -> str:
        return "quiet_steps"


@dataclass(frozen=True)
class UseLure:
    """Drop a lineage lure specifying traits at digits 0..lure_depth-1."""
    lure_ball: Ball

    def action_type(self) -> str:
        return "lure"


@dataclass(frozen=True)
class BranchKeyAction:
    """Unlock a door toggling digit `target_digit`."""
    target_digit: int

    def action_type(self) -> str:
        return "branch_key"


@dataclass(frozen=True)
class RearrangeAction:
    """Apply an affine isometry to the entire world graph."""
    door: AffineDoor
    name: str = "Rearrangement"

    def action_type(self) -> str:
        return "rearrange"


@dataclass(frozen=True)
class ContractAction:
    """Apply 2x contraction (x -> 2x mod 2^depth)."""
    def action_type(self) -> str:
        return "contract"


@dataclass(frozen=True)
class WaitAction:
    def action_type(self) -> str:
        return "wait"
