import pygame
from dataclasses import dataclass
from binary_house.core.address import Address
from binary_house.ui.assets import render_composite_room_art

@dataclass
class Transition:
    """Layer-preserving room transition animation manager."""
    from_addr: Address
    to_addr: Address
    digit_changed: int
    duration_ms: float
    elapsed_ms: float = 0.0

    @classmethod
    def create(cls, from_addr: Address, to_addr: Address, digit_changed: int) -> "Transition":
        # Scale animation duration to mathematical move magnitude
        if digit_changed == 0:
            duration = 800.0  # Structural
        elif digit_changed == 1:
            duration = 500.0  # Regional
        elif digit_changed == 2:
            duration = 350.0  # Local
        else:
            duration = 200.0  # Deep

        return cls(
            from_addr=from_addr,
            to_addr=to_addr,
            digit_changed=digit_changed,
            duration_ms=duration,
        )

    def update(self, dt_ms: float) -> bool:
        """Update animation timer. Returns True when transition completes."""
        self.elapsed_ms += dt_ms
        return self.elapsed_ms >= self.duration_ms

    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed_ms / self.duration_ms)

    def render(self, surface: pygame.Surface, rect: pygame.Rect):
        """Render crossfade transition preserving stable lower layers."""
        p = self.progress

        # Offscreen surfaces for blend
        surf_from = pygame.Surface((rect.width, rect.height))
        surf_to = pygame.Surface((rect.width, rect.height))
        
        render_composite_room_art(surf_from, self.from_addr, pygame.Rect(0, 0, rect.width, rect.height))
        render_composite_room_art(surf_to, self.to_addr, pygame.Rect(0, 0, rect.width, rect.height))

        # Alpha lerp
        surf_to.set_alpha(int(p * 255))
        
        surface.blit(surf_from, rect)
        surface.blit(surf_to, rect)
