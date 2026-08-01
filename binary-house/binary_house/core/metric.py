from binary_house.core.address import Address

def valuation_2(n: int) -> int:
    """Return the 2-adic valuation v₂(n), the exponent of the highest power of 2 dividing n.
    
    Raises ValueError if n == 0 (v₂(0) = +infinity).
    """
    if n == 0:
        raise ValueError("v2(0) is infinite")
    
    # Handle negative integers via magnitude in Z
    n = abs(n)
    count = 0
    while n % 2 == 0:
        n //= 2
        count += 1
    return count


def distance_level(a: Address, b: Address) -> int | None:
    """Return the first differing near-digit index k in [0, depth), or None if identical.
    
    The 2-adic distance is 2^(-distance_level(a, b)).
    Game systems work with this integer level k rather than floating point values.
    """
    if a.depth != b.depth:
        raise ValueError(f"Addresses must have matching depth ({a.depth} vs {b.depth})")

    diff = (a.value - b.value) % (1 << a.depth)
    if diff == 0:
        return None

    val = valuation_2(diff)
    return min(val, a.depth - 1)


def distance_float(a: Address, b: Address) -> float:
    """Return floating point 2-adic distance: 2^(-k), or 0.0 if identical."""
    level = distance_level(a, b)
    if level is None:
        return 0.0
    return 2.0 ** (-level)
