import pytest
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.game.lure import LureRegion
from binary_house.game.caretaker import CaretakerState
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import UseLure

def test_lure_region_timer():
    lure = LureRegion(ball=Ball(residue=0, depth=2, total_depth=4))
    assert lure.tick() is True   # remaining: 2
    assert lure.tick() is True   # remaining: 1
    assert lure.tick() is False  # remaining: 0 (expired)

def test_caretaker_attracted_to_lure():
    caretaker = CaretakerState(
        address=Address(0, depth=4),
        detection_depth=2,
        search_ball=Ball(residue=0, depth=1, total_depth=4),
    )
    # Lure set to opposite branch (residue 1 at depth 1)
    lure_ball = Ball(residue=1, depth=1, total_depth=4)
    lure = LureRegion(ball=lure_ball)

    caretaker.update_search(sound_regions=[], player_address=Address(0, depth=4), lure_regions=[lure])
    assert caretaker.search_ball == lure_ball

def test_use_lure_action():
    world = generate_world(depth=4, seed=42)
    state = GameState.create(world, enable_caretaker=True)
    state.resources["address_lens"] = 1

    lure_ball = Ball(residue=1, depth=2, total_depth=4)
    state.step(UseLure(lure_ball=lure_ball))

    assert len(state.lure_regions) == 1
    assert state.caretaker.search_ball == lure_ball
