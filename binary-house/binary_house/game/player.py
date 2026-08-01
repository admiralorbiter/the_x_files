from dataclasses import dataclass
from typing import Protocol
from binary_house.core.door import ToggleDigit

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
class WaitAction:
    def action_type(self) -> str:
        return "wait"
