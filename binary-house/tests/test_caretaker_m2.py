import pytest
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.game.caretaker import CaretakerState

def test_caretaker_frustration_widen():
    caretaker = CaretakerState(
        address=Address(0, depth=6),
        detection_depth=3,
        search_ball=Ball(residue=0, depth=4, total_depth=6),
    )
    assert caretaker.search_ball.depth == 4
    
    # 3 silent turns tick frustration and widen search ball
    caretaker.update_search(sound_regions=[], player_address=Address(10, depth=6))
    caretaker.update_search(sound_regions=[], player_address=Address(10, depth=6))
    assert caretaker.search_ball.depth == 4
    
    caretaker.update_search(sound_regions=[], player_address=Address(10, depth=6))
    # After 3 silent turns, search ball widens to depth 3
    assert caretaker.search_ball.depth == 3

def test_caretaker_recognized_layers():
    caretaker = CaretakerState(
        address=Address(0b0011, depth=4),
        detection_depth=3,
        search_ball=Ball(residue=0, depth=0, total_depth=4),
    )
    player = Address(0b0001, depth=4)  # b0=1, b1=0, b2=0, b3=0
    
    # Caretaker at b0=1, b1=1, b2=0, b3=0
    # Shared up to detection depth 3: digit 0 (both 1), digit 2 (both 0). Digit 1 differs (0 vs 1).
    recognized = caretaker.recognized_layers(player, depth=4)
    assert recognized == [0, 2]
