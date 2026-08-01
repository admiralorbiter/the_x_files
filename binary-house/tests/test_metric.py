import pytest
from binary_house.core.address import Address
from binary_house.core.metric import valuation_2, distance_level, distance_float

def test_valuation_2():
    assert valuation_2(1) == 0
    assert valuation_2(2) == 1
    assert valuation_2(3) == 0
    assert valuation_2(4) == 2
    assert valuation_2(8) == 3
    assert valuation_2(24) == 3  # 24 = 3 * 8
    with pytest.raises(ValueError):
        valuation_2(0)

def test_distance_level_identical():
    a = Address(42, depth=8)
    b = Address(42, depth=8)
    assert distance_level(a, b) is None
    assert distance_float(a, b) == 0.0

def test_distance_level_spec_example():
    # From spec section 4, panel A example:
    # A = 1·0·1·1·0·0·1·0 (near-first) => bin: 01001101 (LSD=1 on right in std bin)
    # Bit 0..7: 1, 0, 1, 1, 0, 0, 1, 0
    # A value = 1 + 4 + 8 + 64 = 77
    # B = 1·0·1·0·1·1·0·1 => bits: 1, 0, 1, 0, 1, 1, 0, 1
    # B value = 1 + 4 + 16 + 32 + 128 = 181
    # C = 0·1·1·0·0·1·1·0 => bits: 0, 1, 1, 0, 0, 1, 1, 0
    # C value = 2 + 4 + 32 + 64 = 102
    
    A = Address(sum(b << i for i, b in enumerate([1, 0, 1, 1, 0, 0, 1, 0])), depth=8)
    B = Address(sum(b << i for i, b in enumerate([1, 0, 1, 0, 1, 1, 0, 1])), depth=8)
    C = Address(sum(b << i for i, b in enumerate([0, 1, 1, 0, 0, 1, 1, 0])), depth=8)

    # A and B agree for 3 digits (bits 0,1,2 = 1,0,1), differ at digit 3
    assert distance_level(A, B) == 3
    assert distance_float(A, B) == 2.0 ** -3

    # A and C differ at digit 0 (bit 0: 1 vs 0)
    assert distance_level(A, C) == 0
    assert distance_float(A, C) == 1.0

def test_toggle_digit_distance():
    # Test invariant d(x, x XOR 2^k) = 2^(-k) for all x, k in 6-bit world
    depth = 6
    num_rooms = 1 << depth
    for x_val in range(num_rooms):
        x = Address(x_val, depth=depth)
        for k in range(depth):
            y = Address(x_val ^ (1 << k), depth=depth)
            assert distance_level(x, y) == k

def test_strong_triangle_inequality_exhaustive_6bit():
    # Exhaustive verification of strong triangle inequality on 6-bit world (64^3 triples):
    # d(x, z) <= max(d(x, y), d(y, z))
    # In distance levels: distance_level(x, z) >= min(distance_level(x, y), distance_level(y, z))
    depth = 6
    num_rooms = 1 << depth
    addresses = [Address(v, depth=depth) for v in range(num_rooms)]

    for x in addresses:
        for y in addresses:
            d_xy = distance_level(x, y)
            for z in addresses:
                d_yz = distance_level(y, z)
                d_xz = distance_level(x, z)

                if d_xz is None:
                    # x == z, trivially satisfies 0 <= max(d_xy, d_yz)
                    continue
                if d_xy is None:
                    # x == y => d_xz == d_yz
                    assert d_xz == d_yz
                    continue
                if d_yz is None:
                    # y == z => d_xz == d_xy
                    assert d_xz == d_xy
                    continue

                # Floating distance inequality
                dist_xz = 2.0 ** (-d_xz)
                dist_xy = 2.0 ** (-d_xy)
                dist_yz = 2.0 ** (-d_yz)
                assert dist_xz <= max(dist_xy, dist_yz) + 1e-9
