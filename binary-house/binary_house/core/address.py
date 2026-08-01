from dataclasses import dataclass

@dataclass(frozen=True)
class Address:
    """Represents a finite p-adic address in Z/2^depth Z.
    
    `value` is an integer in [0, 2^depth).
    Low-order binary digits represent early near-scale structure.
    """
    value: int
    depth: int = 8

    def __post_init__(self):
        modulus = 1 << self.depth
        # Mask value to ensure it lies within [0, 2^depth)
        object.__setattr__(self, 'value', self.value % modulus)

    def bit(self, index: int) -> int:
        """Return the binary digit at near-position `index` (0 = least significant bit)."""
        if index < 0 or index >= self.depth:
            raise IndexError(f"Bit index {index} out of range for depth {self.depth}")
        return (self.value >> index) & 1

    def prefix(self, k: int) -> int:
        """Return the integer formed by the first k near digits (0 <= k <= depth)."""
        if k < 0 or k > self.depth:
            raise IndexError(f"Prefix depth {k} out of range [0, {self.depth}]")
        if k == 0:
            return 0
        mask = (1 << k) - 1
        return self.value & mask

    def near_first_str(self) -> str:
        """Return string representation in near-first order: b₀ · b₁ · … · b_{depth-1}."""
        return " · ".join(str(self.bit(i)) for i in range(self.depth))

    def __repr__(self) -> str:
        return f"Address({self.near_first_str()}, depth={self.depth})"
