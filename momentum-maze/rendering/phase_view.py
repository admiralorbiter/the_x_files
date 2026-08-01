import math
from typing import List, Optional, Tuple, Dict, Any
import pygame
from simulation.state import PendulumState, PendulumParameters, wrap_theta
from .vector_field import VectorFieldRenderer


class PhaseView:
    def __init__(
        self,
        rect: pygame.Rect,
        theta_range: Tuple[float, float] = (-math.pi, math.pi),
        omega_range: Tuple[float, float] = (-4.0, 4.0),
    ):
        self.rect = rect
        self.theta_min, self.theta_max = theta_range
        self.omega_min, self.omega_max = omega_range
        self.vector_field = VectorFieldRenderer(
            theta_range=theta_range,
            omega_range=omega_range,
        )

        self.font = pygame.font.SysFont("Consolas", 14)
        self.title_font = pygame.font.SysFont("Verdana", 16, bold=True)

    def to_screen(self, theta: float, omega: float) -> Tuple[int, int]:
        """Maps phase point (θ, ω) to screen pixel coordinates."""
        w_theta = wrap_theta(theta)
        dx = self.rect.width / (self.theta_max - self.theta_min)
        dy = self.rect.height / (self.omega_max - self.omega_min)

        px = self.rect.left + (w_theta - self.theta_min) * dx
        py = self.rect.bottom - (omega - self.omega_min) * dy
        return int(px), int(py)

    def draw_grid_and_axes(self, surface: pygame.Surface, show_labels: bool = True):
        """Draws background grid, origin axes, and cylinder seam lines."""
        # Panel background
        pygame.draw.rect(surface, (15, 20, 30), self.rect)
        pygame.draw.rect(surface, (45, 60, 85), self.rect, 2)

        # Origin axes (θ=0, ω=0)
        origin_x, origin_y = self.to_screen(0.0, 0.0)

        # Horizontal axis ω=0
        if self.rect.top <= origin_y <= self.rect.bottom:
            pygame.draw.line(
                surface,
                (60, 80, 110),
                (self.rect.left, origin_y),
                (self.rect.right, origin_y),
                1,
            )

        # Vertical axis θ=0
        if self.rect.left <= origin_x <= self.rect.right:
            pygame.draw.line(
                surface,
                (60, 80, 110),
                (origin_x, self.rect.top),
                (origin_x, self.rect.bottom),
                1,
            )

        # Cylinder Seam Lines (θ = ±π)
        seam_left_x, _ = self.to_screen(-math.pi, 0.0)
        seam_right_x, _ = self.to_screen(math.pi - 1e-4, 0.0)

        # Dashed seam indicators
        for y in range(self.rect.top, self.rect.bottom, 10):
            pygame.draw.line(surface, (120, 90, 180), (self.rect.left, y), (self.rect.left, y + 5), 2)
            pygame.draw.line(surface, (120, 90, 180), (self.rect.right - 2, y), (self.rect.right - 2, y + 5), 2)

        if show_labels:
            title = self.title_font.render("PHASE DUNGEON (θ, ω)", True, (180, 200, 230))
            surface.blit(title, (self.rect.left + 15, self.rect.top + 12))

            # Axis ticks & labels
            lbl_w = self.font.render("ω ↑", True, (140, 160, 190))
            surface.blit(lbl_w, (origin_x + 6, self.rect.top + 12))

            lbl_t_neg = self.font.render("-π", True, (160, 140, 200))
            lbl_t_zero = self.font.render("0", True, (140, 160, 190))
            lbl_t_pos = self.font.render("+π", True, (160, 140, 200))

            surface.blit(lbl_t_neg, (self.rect.left + 8, origin_y + 6))
            surface.blit(lbl_t_zero, (origin_x + 4, origin_y + 6))
            surface.blit(lbl_t_pos, (self.rect.right - 28, origin_y + 6))

    def draw_constraints(self, surface: pygame.Surface, constraints: List[Any]):
        """Renders phase space gates, hazards, docks, and key zones."""
        for c in constraints:
            c.draw_phase(surface, self)

    def draw_trajectory_trail(self, surface: pygame.Surface, trail: List[PendulumState]):
        """Draws historical state motion trail."""
        if len(trail) < 2:
            return

        for i in range(len(trail) - 1):
            s1, s2 = trail[i], trail[i + 1]

            # Check for angle wrap jump
            if abs(wrap_theta(s1.theta) - wrap_theta(s2.theta)) > math.pi:
                continue

            pt1 = self.to_screen(s1.theta, s1.omega)
            pt2 = self.to_screen(s2.theta, s2.omega)

            alpha = int(255 * ((i + 1) / len(trail)))
            color = (100, 220, 255)
            pygame.draw.line(surface, color, pt1, pt2, 2)

    def draw_candidate_predictions(
        self,
        surface: pygame.Surface,
        predictions: Dict[float, List[PendulumState]],
        selected_torque: float,
    ):
        """
        Draws predicted candidate trajectories for u ∈ {-u_max, 0, +u_max}.
        The selected action is highlighted brightly; others are subdued.
        """
        color_map = {
            -0.35: (240, 80, 80),   # Left torque
            0.0: (220, 220, 100),   # Coast / Neutral
            0.35: (80, 220, 120),   # Right torque
        }

        for torque, traj in predictions.items():
            if len(traj) < 2:
                continue

            is_selected = abs(torque - selected_torque) < 1e-4
            base_color = color_map.get(round(torque, 2), (200, 200, 200))

            if is_selected:
                color = base_color
                width = 3
            else:
                # Subdued
                color = tuple(int(c * 0.45) for c in base_color)
                width = 1

            for i in range(len(traj) - 1):
                s1, s2 = traj[i], traj[i + 1]
                if abs(wrap_theta(s1.theta) - wrap_theta(s2.theta)) > math.pi:
                    continue

                pt1 = self.to_screen(s1.theta, s1.omega)
                pt2 = self.to_screen(s2.theta, s2.omega)

                # Differentiate pulse duration (first segment) from coast tail
                is_pulse_segment = i < int(0.35 / (1.0 / 240.0))

                if is_selected:
                    seg_color = color if is_pulse_segment else tuple(int(c * 0.65) for c in color)
                    pygame.draw.line(surface, seg_color, pt1, pt2, width)
                else:
                    if i % 3 != 0:  # Dashed line for unselected
                        pygame.draw.line(surface, color, pt1, pt2, width)

    def draw_current_state(self, surface: pygame.Surface, state: PendulumState):
        """Draws glowing current state marker."""
        px, py = self.to_screen(state.theta, state.omega)

        # Outer glow
        glow_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (0, 230, 255, 60), (16, 16), 14)
        pygame.draw.circle(glow_surf, (0, 230, 255, 140), (16, 16), 9)
        surface.blit(glow_surf, (px - 16, py - 16))

        # Core dot
        pygame.draw.circle(surface, (255, 255, 255), (px, py), 5)
        pygame.draw.circle(surface, (0, 220, 255), (px, py), 3)
