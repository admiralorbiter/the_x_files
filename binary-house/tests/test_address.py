import pytest
from binary_house.core.address import Address

def test_address_creation():
    addr = Address(0b10110010, depth=8)
    assert addr.value == 0b10110010
    assert addr.depth == 8

def test_address_wrapping():
    addr = Address(258, depth=8)
    assert addr.value == 2  # 258 % 256 == 2

def test_bit_extraction():
    # Value 0b10110010: b0=0, b1=1, b2=0, b3=0, b4=1, b5=1, b6=0, b7=1
    addr = Address(0b10110010, depth=8)
    assert addr.bit(0) == 0
    assert addr.bit(1) == 1
    assert addr.bit(2) == 0
    assert addr.bit(3) == 0
    assert addr.bit(4) == 1
    assert addr.bit(5) == 1
    assert addr.bit(6) == 0
    assert addr.bit(7) == 1

def test_bit_index_error():
    addr = Address(5, depth=4)
    with pytest.raises(IndexError):
        addr.bit(4)
    with pytest.raises(IndexError):
        addr.bit(-1)

def test_prefix_extraction():
    addr = Address(0b10110010, depth=8)
    assert addr.prefix(0) == 0
    assert addr.prefix(1) == 0  # bit 0 = 0
    assert addr.prefix(2) == 0b10  # bits 0,1 = 0, 1 -> 2
    assert addr.prefix(4) == 0b0010  # bits 0..3 = 2
    assert addr.prefix(8) == 0b10110010

def test_near_first_formatting():
    # 0b00001011 (value 11): b0=1, b1=1, b2=0, b3=1, b4=0, b5=0, b6=0, b7=0
    addr = Address(11, depth=8)
    assert addr.near_first_str() == "1 · 1 · 0 · 1 · 0 · 0 · 0 · 0"
