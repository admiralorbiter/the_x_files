import pytest
from binary_house.core.address import Address
from binary_house.core.contraction import contract_2x

def test_contraction_2x():
    addr_0 = Address(0b0001, depth=4)  # Wooden Foundation (b0=1)
    addr_1 = Address(0b0000, depth=4)  # Wooden Foundation (b0=0)
    
    c_0 = contract_2x(addr_0)
    c_1 = contract_2x(addr_1)
    
    # 2 * 1 mod 16 = 2 (even)
    assert c_0.value == 2
    # 2 * 0 mod 16 = 0 (even)
    assert c_1.value == 0
    
    # Both contracted values are even
    assert c_0.bit(0) == 0
    assert c_1.bit(0) == 0
