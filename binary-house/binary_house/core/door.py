from dataclasses import dataclass
from typing import Protocol
from binary_house.core.address import Address

class DoorOperation(Protocol):
    """Protocol for doors that transform an address."""
    def apply(self, address: Address) -> Address:
        ...

    def distance_level(self) -> int:
        """The 2-adic distance level of this move."""
        ...

    def noise_depth(self) -> int:
        """The initial neighborhood depth that sound/noise fills."""
        ...


@dataclass(frozen=True)
class ToggleDigit:
    """Standard 1-bit door operation: x -> x XOR 2^index.
    
    Flips the bit at `index` (0 = nearest, low-order digit).
    Distance of move is 2^(-index).
    """
    index: int

    def apply(self, address: Address) -> Address:
        if self.index < 0 or self.index >= address.depth:
            raise IndexError(f"Door digit index {self.index} out of range for depth {address.depth}")
        new_val = address.value ^ (1 << self.index)
        return Address(value=new_val, depth=address.depth)

    def distance_level(self) -> int:
        return self.index

    def noise_depth(self) -> int:
        return self.index


@dataclass(frozen=True)
class AffineDoor:
    """Affine transformation door: x -> (multiplier * x + offset) mod 2^depth.
    
    If multiplier is odd, this is an isometry (distance-preserving permutation of Z/2^n Z).
    """
    multiplier: int
    offset: int

    def __post_init__(self):
        if self.multiplier % 2 == 0:
            raise ValueError("Multiplier must be odd for an affine isometry")

    def apply(self, address: Address) -> Address:
        modulus = 1 << address.depth
        new_val = (self.multiplier * address.value + self.offset) % modulus
        return Address(value=new_val, depth=address.depth)

    def distance_level(self) -> int:
        # Affine isometric maps preserve distance globally
        return 0

    def noise_depth(self) -> int:
        return 0
