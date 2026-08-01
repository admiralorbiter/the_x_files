import pytest
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit
from binary_house.core.ball import Ball
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction, UseChalk, UseQuietSteps, BranchKeyAction

def test_quiet_steps_reduces_noise():
    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=False)
    state.resources["quiet_steps"] = 1

    door = ToggleDigit(0)  # Front Door (normally loud sound_depth 0)
    event = state.step(UseQuietSteps(door))
    
    assert event.sound_depth == 0  # max(0, 0 - 2) = 0
    assert state.resources["quiet_steps"] == 0

def test_use_chalk():
    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=False)
    state.resources["chalk"] = 1

    state.step(UseChalk(depth=2))
    assert state.resources["chalk"] == 0
    assert len(state.chalk_marks) == 1

def test_branch_key():
    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=False)
    state.resources["branch_key"] = 1

    event = state.step(BranchKeyAction(target_digit=3))
    assert event.move_scale == 3
    assert state.resources["branch_key"] == 0
