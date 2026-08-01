from binary_house.core.address import Address

def contract_2x(address: Address) -> Address:
    """Apply 2-adic contraction x -> (2 * x) mod 2^depth.
    
    This contracts the space by factor 2:
    - Collapses b₀ (Wooden and Stone Foundations map to the same address).
    - Maps all addresses to even values mod 2^depth.
    """
    modulus = 1 << address.depth
    new_val = (2 * address.value) % modulus
    return Address(new_val, depth=address.depth)
