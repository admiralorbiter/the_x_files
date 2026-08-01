from dataclasses import dataclass
from typing import Literal
from binary_house.core.address import Address

@dataclass(frozen=True)
class Ball:
    """Represents a 2-adic neighborhood B_k(x) defined by a fixed prefix.
    
    `residue` is the fixed near-digit prefix value.
    `depth` is the number of fixed digits (0 <= depth <= total_space_depth).
    `total_depth` is the dimension of the containing space (default 8).
    """
    residue: int
    depth: int
    total_depth: int = 8

    def __post_init__(self):
        if self.depth < 0 or self.depth > self.total_depth:
            raise ValueError(f"Ball depth {self.depth} invalid for total depth {self.total_depth}")
        mask = (1 << self.depth) - 1 if self.depth > 0 else 0
        object.__setattr__(self, 'residue', self.residue & mask)

    def contains(self, address: Address) -> bool:
        """Check if an address is inside this neighborhood ball."""
        if address.depth != self.total_depth:
            raise ValueError(f"Address depth {address.depth} mismatch with ball total depth {self.total_depth}")
        return address.prefix(self.depth) == self.residue

    def size(self) -> int:
        """Number of leaf rooms in this ball (2^(total_depth - depth))."""
        return 1 << (self.total_depth - self.depth)

    def parent(self) -> "Ball | None":
        """Return the immediate containing parent ball at depth - 1, or None if at root."""
        if self.depth == 0:
            return None
        return Ball(residue=self.residue, depth=self.depth - 1, total_depth=self.total_depth)

    def children(self) -> tuple["Ball", "Ball"]:
        """Return the two child sub-balls at depth + 1."""
        if self.depth == self.total_depth:
            raise ValueError("Leaf ball has no children")
        next_depth = self.depth + 1
        child0 = Ball(residue=self.residue, depth=next_depth, total_depth=self.total_depth)
        child1 = Ball(residue=self.residue | (1 << self.depth), depth=next_depth, total_depth=self.total_depth)
        return child0, child1

    @staticmethod
    def relationship(a: "Ball", b: "Ball") -> Literal["equal", "nested", "disjoint"]:
        """Determine topological relationship between two ultrametric balls.
        
        Because distance is ultrametric, balls are always either equal, nested, or disjoint.
        Partial overlap never occurs.
        """
        if a.total_depth != b.total_depth:
            raise ValueError("Ball total depth mismatch")

        if a.depth == b.depth:
            return "equal" if a.residue == b.residue else "disjoint"

        shorter, longer = (a, b) if a.depth < b.depth else (b, a)
        mask = (1 << shorter.depth) - 1 if shorter.depth > 0 else 0
        if (longer.residue & mask) == shorter.residue:
            return "nested"
        return "disjoint"
