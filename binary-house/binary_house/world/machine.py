import random
from binary_house.core.door import AffineDoor

class RearrangementMachine:
    """Generates thematic distance-preserving affine isometries for house rearrangement events."""
    
    NAMED_REARRANGEMENTS = [
        {"name": "The Folding", "multiplier": 3, "offset": 1,
         "description": "The house folds. Foundations that were far become near, but distances are preserved."},
        {"name": "The Inversion", "multiplier": 5, "offset": 0,
         "description": "The house inverts. What was deep is now close."},
        {"name": "The Drift", "multiplier": 7, "offset": 3,
         "description": "The house drifts sideways. Your memories are intact, but misplaced."},
    ]
    
    @classmethod
    def get_rearrangement(cls, rng: random.Random) -> dict:
        return rng.choice(cls.NAMED_REARRANGEMENTS)
    
    @classmethod
    def make_door(cls, config: dict) -> AffineDoor:
        return AffineDoor(multiplier=config["multiplier"], offset=config["offset"])
