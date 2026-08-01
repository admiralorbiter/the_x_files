import pytest
from binary_house.core.address import Address
from binary_house.core.metric import distance_level
from binary_house.world.world import generate_world, make_relational_clue

def test_world_generation_seals_distance():
    depth = 6
    world = generate_world(depth=depth, seed=42)
    p_start = world.player_start
    
    expected_levels = [0, max(1, depth // 2), depth - 1]
    
    for idx, seal_addr in enumerate(world.seal_locations):
        dist = distance_level(p_start, seal_addr)
        assert dist == expected_levels[idx]

def test_make_relational_clue():
    player_start = Address(0b0000, depth=4)
    
    # Structural diff (k=0)
    seal_0 = Address(0b0001, depth=4)
    clue_0 = make_relational_clue(seal_0, player_start, 4)
    assert "different Foundation" in clue_0

    # Regional diff (k=1)
    seal_1 = Address(0b0010, depth=4)
    clue_1 = make_relational_clue(seal_1, player_start, 4)
    assert "shares your Foundation" in clue_1
    assert "Wing is Sun Wing" in clue_1
