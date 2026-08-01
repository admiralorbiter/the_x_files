from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.game.sound import SoundRegion
from binary_house.game.lure import LureRegion

if TYPE_CHECKING:
    from binary_house.ui.fiction import FictionMapper

@dataclass
class CaretakerState:
    """The Caretaker AI search state and detection ball."""
    address: Address
    detection_depth: int     # h - detects player when sharing depth-h prefix
    search_ball: Ball        # current belief ball about player's whereabouts
    frustration: int = 0     # turns without hearing sound
    heat: int = 0            # 0 = cold, 3 = max heat
    MAX_HEAT: int = 3

    def increase_heat(self):
        self.heat = min(self.MAX_HEAT, self.heat + 1)

    def decrease_heat(self):
        self.heat = max(0, self.heat - 1)

    @property
    def effective_detection_depth(self) -> int:
        return max(1, self.detection_depth - self.heat)

    def is_detecting(self, player_address: Address) -> bool:
        """Return True if player is inside the Caretaker's detection ball."""
        eff_depth = self.effective_detection_depth
        detection_ball = Ball(
            residue=self.address.prefix(eff_depth),
            depth=eff_depth,
            total_depth=self.address.depth,
        )
        return detection_ball.contains(player_address)

    def recognized_layers(self, player_address: Address, depth: int) -> list[int]:
        """Return indices of digits shared between caretaker and player within detection_depth."""
        return [
            i for i in range(min(self.detection_depth, depth))
            if self.address.bit(i) == player_address.bit(i)
        ]

    def search_wing_name(self, mapper: FictionMapper) -> str:
        """Return fiction description of search ball."""
        return mapper.wing_name(self.search_ball)

    def tick_frustration(self):
        """Call once per turn when no sound is heard. Widens search after threshold."""
        self.frustration += 1
        if self.frustration >= 3:
            parent = self.search_ball.parent()
            if parent is not None:
                self.search_ball = parent
            self.frustration = 0

    def update_search(self, sound_regions: list[SoundRegion], player_address: Address, lure_regions: list[LureRegion] | None = None):
        """Update search ball based on lures or sound signals."""
        sound_heard = False

        # 1. High priority: check lineage lures first
        if lure_regions:
            for lure in lure_regions:
                sound_heard = True
                self.frustration = 0
                self.increase_heat()
                self.search_ball = lure.ball
                break

        # 2. Secondary priority: sound signals
        if not sound_heard:
            for sound in sound_regions:
                if sound.ball.contains(self.address):
                    sound_heard = True
                    self.frustration = 0
                    self.increase_heat()
                    if sound.ball.depth > self.search_ball.depth:
                        self.search_ball = sound.ball
                    break
        
        if not sound_heard:
            self.decrease_heat()
            self.tick_frustration()

    def act(self, depth: int) -> Address:
        """Deterministic move toward search ball.
        
        Prefers local low-cost moves (flipping high-index digits first).
        """
        if self.search_ball.contains(self.address):
            return self.address

        # Target residue bit by bit from low-order to high-order
        for k in range(depth):
            if self.address.bit(k) != ((self.search_ball.residue >> k) & 1):
                new_val = self.address.value ^ (1 << k)
                self.address = Address(new_val, depth=depth)
                return self.address

        return self.address
