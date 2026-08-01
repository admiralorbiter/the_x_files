import pytest
from binary_house.core.address import Address
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction
from binary_house.core.door import ToggleDigit

def test_caretaker_detection():
    world = generate_world(depth=6, seed=42)
    state = GameState.create(world, enable_caretaker=True)
    
    # Force caretaker detection depth to 4
    state.caretaker.detection_depth = 4
    state.caretaker.address = Address(0b001101, depth=6)
    
    # Player sharing first 4 bits (0b1101 = bits 0..3)
    player_detectable = Address(0b101101, depth=6)  # bits 0..3 match 1101
    player_safe = Address(0b100000, depth=6)        # bits 0..3 match 0000
    
    assert state.caretaker.is_detecting(player_detectable)
    assert not state.caretaker.is_detecting(player_safe)

def test_game_turn_sequence():
    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=False)
    
    initial_addr = state.player_address
    door = ToggleDigit(0)
    event = state.step(MoveAction(door))
    
    assert event.turn == 1
    assert state.player_address.value == initial_addr.value ^ 1
    assert event.move_scale == 0
    assert len(state.event_log) == 1
