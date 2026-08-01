import pytest
from binary_house.core.address import Address
from binary_house.core.door import AffineDoor
from binary_house.core.metric import distance_level
from binary_house.world.world import generate_world
from binary_house.game.state import GameState
from binary_house.game.player import RearrangeAction, ContractAction

def test_rearrangement_preserves_distances():
    world = generate_world(depth=6, seed=42)
    state = GameState.create(world, enable_caretaker=True)
    
    # Check distance to Caretaker before rearrangement
    dist_before = distance_level(state.player_address, state.caretaker.address)
    seal_dists_before = [distance_level(state.player_address, s) for s in state.world.seal_locations]
    
    # Perform affine isometric house rearrangement (multiplier=3, offset=1)
    door = AffineDoor(multiplier=3, offset=1)
    state.step(RearrangeAction(door=door, name="The Folding"))
    
    # Check distance to Caretaker after rearrangement
    dist_after = distance_level(state.player_address, state.caretaker.address)
    seal_dists_after = [distance_level(state.player_address, s) for s in state.world.seal_locations]
    
    # Affine isometry MUST preserve all distances
    assert dist_before == dist_after
    assert seal_dists_before == seal_dists_after

def test_contraction_action():
    world = generate_world(depth=6, seed=42)
    state = GameState.create(world, enable_caretaker=True)
    initial_detection_depth = state.caretaker.detection_depth
    
    state.step(ContractAction())
    
    assert state.caretaker.detection_depth == max(1, initial_detection_depth - 1)
