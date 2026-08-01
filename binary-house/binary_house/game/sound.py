from dataclasses import dataclass
from binary_house.core.ball import Ball

@dataclass
class SoundRegion:
    """Represents a noise event that originates in a ball and leaks outward through parent balls."""
    ball: Ball
    age: int = 0
    max_age: int = 4

    def expand(self) -> "SoundRegion | None":
        """Expand noise to containing parent ball. Returns None if already at root or expired."""
        if self.age >= self.max_age:
            return None
        parent_ball = self.ball.parent()
        if parent_ball is None:
            return None
        return SoundRegion(ball=parent_ball, age=self.age + 1, max_age=self.max_age)
