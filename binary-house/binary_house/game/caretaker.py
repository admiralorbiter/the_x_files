from dataclasses import dataclass
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.game.sound import SoundRegion

@dataclass
class CaretakerState:
    """The Caretaker AI search state and detection ball."""
    address: Address
    detection_depth: int     # h - detects player when sharing depth-h prefix
    search_ball: Ball        # current belief ball about player's whereabouts

    def is_detecting(self, player_address: Address) -> bool:
        """Return True if player is inside the Caretaker's detection ball."""
        detection_ball = Ball(
            residue=self.address.prefix(self.detection_depth),
            depth=self.detection_depth,
            total_depth=self.address.depth,
        )
        return detection_ball.contains(player_address)

    def update_search(self, sound_regions: list[SoundRegion], player_address: Address):
        """Update search ball based on sound signals."""
        for sound in sound_regions:
            if sound.ball.contains(self.address):
                # Sound heard! Narrow search ball to sound region if smaller
                if sound.ball.depth > self.search_ball.depth:
                    self.search_ball = sound.ball
                break

    def act(self, depth: int) -> Address:
        """Deterministic move toward search ball.
        
        Prefers local low-cost moves (flipping high-index digits first).
        """
        if self.search_ball.contains(self.address):
            # Already inside belief ball - narrow search further if depth permits
            if self.search_ball.depth < depth:
                # Pick child containing current address
                pass
            return self.address

        # Target residue bit by bit from low-order to high-order
        for k in range(depth):
            if self.address.bit(k) != ((self.search_ball.residue >> k) & 1):
                # Flip digit k to match target prefix
                new_val = self.address.value ^ (1 << k)
                self.address = Address(new_val, depth=depth)
                return self.address

        return self.address
