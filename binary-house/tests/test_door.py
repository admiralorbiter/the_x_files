import pytest
from binary_house.core.address import Address
from binary_house.core.metric import distance_level
from binary_house.core.door import ToggleDigit, AffineDoor

def test_toggle_digit():
    addr = Address(0b1010, depth=4)
    door = ToggleDigit(index=1)
    new_addr = door.apply(addr)
    
    # 0b1010 ^ 0b0010 = 0b1000
    assert new_addr.value == 0b1000
    assert door.distance_level() == 1
    assert distance_level(addr, new_addr) == 1

def test_affine_door_isometry():
    depth = 6
    num_rooms = 1 << depth
    # x -> (3x + 5) mod 64
    door = AffineDoor(multiplier=3, offset=5)

    addrs = [Address(v, depth=depth) for v in range(num_rooms)]
    mapped_addrs = [door.apply(a) for a in addrs]

    # Verify permutation
    assert len(set(a.value for a in mapped_addrs)) == num_rooms

    # Verify distance preservation for all pairs
    for i in range(num_rooms):
        for j in range(i + 1, num_rooms):
            orig_d = distance_level(addrs[i], addrs[j])
            mapped_d = distance_level(mapped_addrs[i], mapped_addrs[j])
            assert orig_d == mapped_d

def test_even_multiplier_rejected():
    with pytest.raises(ValueError):
        AffineDoor(multiplier=2, offset=1)
