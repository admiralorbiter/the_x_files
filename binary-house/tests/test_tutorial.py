import pytest
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction
from binary_house.ui.tutorial import TutorialState

def test_tutorial_advancement():
    tutorial = TutorialState()
    assert tutorial.current_scene == 0
    assert tutorial.get_current()["expected_digit"] == 3

    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=False)

    # Wrong move (digit 0) does not advance scene 0
    event_wrong = state.step(MoveAction(ToggleDigit(0)))
    assert not tutorial.advance(event_wrong, state)
    assert tutorial.current_scene == 0

    # Correct move (digit 3) advances scene 0 -> scene 1
    event_correct = state.step(MoveAction(ToggleDigit(3)))
    assert tutorial.advance(event_correct, state)
    assert tutorial.current_scene == 1
