import pytest
from binary_house.core.metric import distance_level
from binary_house.world.world import generate_world
from binary_house.game.caretaker import CaretakerState
from binary_house.core.address import Address
from binary_house.core.ball import Ball

def test_m4_8bit_world_generation():
    world = generate_world(depth=8, seed=42)
    assert world.depth == 8
    assert len(world.seal_locations) == 5
    
    expected_levels = [0, 1, 3, 5, 7]
    for idx, seal_addr in enumerate(world.seal_locations):
        dist = distance_level(world.player_start, seal_addr)
        assert dist == expected_levels[idx]

def test_caretaker_heat_system():
    caretaker = CaretakerState(
        address=Address(0, depth=8),
        detection_depth=4,
        search_ball=Ball(residue=0, depth=4, total_depth=8),
    )
    assert caretaker.heat == 0
    assert caretaker.effective_detection_depth == 4

    caretaker.increase_heat()
    assert caretaker.heat == 1
    assert caretaker.effective_detection_depth == 3  # broader detection ball

    caretaker.decrease_heat()
    assert caretaker.heat == 0
    assert caretaker.effective_detection_depth == 4
