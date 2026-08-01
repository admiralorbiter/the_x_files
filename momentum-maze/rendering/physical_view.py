import math
from typing import List, Optional, Tuple, Any
import pygame
from simulation.state import PendulumState, wrap_theta


class PhysicalView:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.pivot_x = rect.centerx
        self.pivot_y = rect.centery
        self.arm_length = int(min(rect.width, rect.height) * 0.35)
        self.bob_radius = 16

        self.font = pygame.font.SysFont("Consolas", 14)
        self.title_font = pygame.font.SysFont("Verdana", 16, bold=True)

    def get_bob_position(self, theta: float) -> Tuple[int, int]:
        """
        Computes physical bob (x, y) coordinates for angle θ.
        θ = 0 is straight down. Positive θ is counterclockwise (to the right initially).
        """
        w_theta = wrap_theta(theta)
        # θ = 0 is down: x = pivot_x + L * sin(θ), y = pivot_y + L * cos(θ)
        bx = self.pivot_x + self.arm_length * math.sin(w_theta)
        by = self.pivot_y + self.arm_length * math.cos(w_theta)
        return int(bx), int(by)

    def draw_background_and_ticks(self, surface: pygame.Surface):
        """Draws background panel, pivot, and angle reference marks."""
        pygame.draw.rect(surface, (15, 20, 30), self.rect)
        pygame.draw.rect(surface, (45, 60, 85), self.rect, 2)

        # Title
        title = self.title_font.render("PHYSICAL MECHANISM", True, (180, 200, 230))
        surface.blit(title, (self.rect.left + 15, self.rect.top + 12))

        # Circular arc trajectory reference track
        pygame.draw.circle(
            surface,
            (30, 45, 65),
            (self.pivot_x, self.pivot_y),
            self.arm_length,
            1,
        )

        # Reference tick marks: θ=0 (Down), θ=π (Up), θ=π/2 (Right), θ=-π/2 (Left)
        ticks = [
            (0.0, "0 (Down)"),
            (math.pi, "π (Up)"),
            (math.pi / 2.0, "+π/2"),
            (-math.pi / 2.0, "-π/2"),
        ]

        for angle, label in ticks:
            tx = self.pivot_x + (self.arm_length + 12) * math.sin(angle)
            ty = self.pivot_y + (self.arm_length + 12) * math.cos(angle)

            # Short tick line
            inner_x = self.pivot_x + (self.arm_length - 6) * math.sin(angle)
            inner_y = self.pivot_y + (self.arm_length - 6) * math.cos(angle)
            pygame.draw.line(surface, (70, 90, 120), (inner_x, inner_y), (tx, ty), 2)

            # Label text
            lbl = self.font.render(label, True, (120, 140, 170))
            lbl_rect = lbl.get_rect(center=(int(tx), int(ty)))
            surface.blit(lbl, lbl_rect)

    def draw_constraints(self, surface: pygame.Surface, constraints: List[Any]):
        """Renders physical counterparts of state gates and targets on the arc."""
        for c in constraints:
            c.draw_physical(surface, self)

    def draw_afterimages(self, surface: pygame.Surface, trail: List[PendulumState]):
        """Draws ghost bob afterimages for recent motion."""
        if len(trail) < 2:
            return

        # Draw subset of recent states as ghost bobs
        step = max(1, len(trail) // 6)
        for i in range(0, len(trail), step):
            s = trail[i]
            bx, by = self.get_bob_position(s.theta)
            alpha = int(120 * ((i + 1) / len(trail)))

            ghost_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (0, 180, 240, alpha), (16, 16), 10)
            surface.blit(ghost_surf, (bx - 16, by - 16))

    def draw_pendulum(
        self,
        surface: pygame.Surface,
        state: PendulumState,
        applied_torque: float = 0.0,
    ):
        """Draws physical rod, bob, pivot, and torque indicator."""
        bx, by = self.get_bob_position(state.theta)

        # Rigid rod
        pygame.draw.line(
            surface,
            (200, 215, 235),
            (self.pivot_x, self.pivot_y),
            (bx, by),
            4,
        )

        # Torque indicator arc around pivot
        if abs(applied_torque) > 1e-4:
            radius = 28
            is_right = applied_torque > 0
            color = (80, 220, 120) if is_right else (240, 80, 80)

            start_ang = -math.pi / 2
            end_ang = start_ang + (0.8 * math.pi if is_right else -0.8 * math.pi)

            rect = pygame.Rect(
                self.pivot_x - radius,
                self.pivot_y - radius,
                radius * 2,
                radius * 2,
            )
            pygame.draw.arc(
                surface,
                color,
                rect,
                min(start_ang, end_ang),
                max(start_ang, end_ang),
                3,
            )

        # Pivot center
        pygame.draw.circle(surface, (240, 240, 250), (self.pivot_x, self.pivot_y), 8)
        pygame.draw.circle(surface, (60, 80, 110), (self.pivot_x, self.pivot_y), 4)

        # Bob glow & core
        glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (0, 220, 255, 70), (24, 24), 22)
        surface.blit(glow_surf, (bx - 24, by - 24))

        pygame.draw.circle(surface, (0, 220, 255), (bx, by), self.bob_radius)
        pygame.draw.circle(surface, (255, 255, 255), (bx, by), self.bob_radius - 5)
