import math
from typing import List, Tuple
import numpy as np
import pygame
from simulation.state import PendulumParameters, wrap_theta


class VectorFieldRenderer:
    def __init__(
        self,
        theta_range: Tuple[float, float] = (-math.pi, math.pi),
        omega_range: Tuple[float, float] = (-4.0, 4.0),
        grid_cols: int = 33,
        grid_rows: int = 25,
    ):
        self.theta_min, self.theta_max = theta_range
        self.omega_min, self.omega_max = omega_range
        self.cols = grid_cols
        self.rows = grid_rows

        # Grid points
        self.thetas = np.linspace(self.theta_min, self.theta_max, self.cols)
        self.omegas = np.linspace(self.omega_min, self.omega_max, self.rows)
        self.THETA, self.OMEGA = np.meshgrid(self.thetas, self.omegas)

    def draw_contours(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        contour_levels: List[float] = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        show_separatrix: bool = True,
    ):
        """
        Draws energy contour lines using Marching Squares algorithm.
        E(θ, ω) = 0.5 * ω² + 1 - cos(θ)
        """
        # Fine grid for high resolution contours
        res_cols, res_rows = 120, 100
        t_fine = np.linspace(self.theta_min, self.theta_max, res_cols)
        w_fine = np.linspace(self.omega_min, self.omega_max, res_rows)
        T_fine, W_fine = np.meshgrid(t_fine, w_fine)
        E = 0.5 * (W_fine**2) + (1.0 - np.cos(T_fine))

        dx = rect.width / (self.theta_max - self.theta_min)
        dy = rect.height / (self.omega_max - self.omega_min)

        def to_screen(t_val: float, w_val: float) -> Tuple[float, float]:
            px = rect.left + (t_val - self.theta_min) * dx
            py = rect.bottom - (w_val - self.omega_min) * dy
            return px, py

        # Simple Marching Squares contour segment extraction
        for level in contour_levels:
            is_separatrix = abs(level - 2.0) < 1e-4
            if is_separatrix and not show_separatrix:
                continue

            color = (235, 180, 50) if is_separatrix else (45, 65, 95)
            width = 3 if is_separatrix else 1

            # Cell edges lookup
            for r in range(res_rows - 1):
                for c in range(res_cols - 1):
                    # Cell corners: bottom-left, bottom-right, top-right, top-left
                    v = [
                        E[r, c],
                        E[r, c + 1],
                        E[r + 1, c + 1],
                        E[r + 1, c],
                    ]
                    pts = [
                        (t_fine[c], w_fine[r]),
                        (t_fine[c + 1], w_fine[r]),
                        (t_fine[c + 1], w_fine[r + 1]),
                        (t_fine[c], w_fine[r + 1]),
                    ]

                    # Find interpolated crossings on edges
                    crossings = []
                    for i in range(4):
                        v1, v2 = v[i], v[(i + 1) % 4]
                        p1, p2 = pts[i], pts[(i + 1) % 4]
                        if (v1 <= level < v2) or (v2 <= level < v1):
                            frac = (level - v1) / (v2 - v1) if v2 != v1 else 0.5
                            tx = p1[0] + frac * (p2[0] - p1[0])
                            wx = p1[1] + frac * (p2[1] - p1[1])
                            crossings.append(to_screen(tx, wx))

                    if len(crossings) == 2:
                        pygame.draw.line(surface, color, crossings[0], crossings[1], width)
                    elif len(crossings) == 4:
                        pygame.draw.line(surface, color, crossings[0], crossings[1], width)
                        pygame.draw.line(surface, color, crossings[2], crossings[3], width)

    def draw_vector_field(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        params: PendulumParameters,
        torque: float = 0.0,
        alpha: int = 140,
    ):
        """
        Draws the phase field vector arrows F(θ, ω; u).
        """
        d_theta = self.OMEGA
        d_omega = (
            -params.gravity_over_length * np.sin(self.THETA)
            - params.damping * self.OMEGA
            + torque
        )

        speeds = np.hypot(d_theta, d_omega)
        max_speed = np.max(speeds) if np.max(speeds) > 0 else 1.0

        dx = rect.width / (self.theta_max - self.theta_min)
        dy = rect.height / (self.omega_max - self.omega_min)

        arrow_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        for r in range(self.rows):
            for c in range(self.cols):
                t_val = self.THETA[r, c]
                w_val = self.OMEGA[r, c]

                dt_val = d_theta[r, c]
                dw_val = d_omega[r, c]
                sp = speeds[r, c]

                if sp < 1e-4:
                    continue

                # Local screen position relative to arrow surface
                px = (t_val - self.theta_min) * dx
                py = rect.height - (w_val - self.omega_min) * dy

                # Normalized arrow vector
                arrow_len = 10.0 + 8.0 * (sp / max_speed)
                u_x = (dt_val / sp) * arrow_len
                u_y = -(dw_val / sp) * arrow_len  # Invert Y for screen coords

                end_x = px + u_x
                end_y = py + u_y

                # Speed-based color
                intensity = int(80 + 175 * (sp / max_speed))
                color = (70, 130, 200, min(alpha, intensity))

                pygame.draw.line(arrow_surface, color, (px, py), (end_x, end_y), 1)
                # Arrowhead
                angle = math.atan2(u_y, u_x)
                h1_x = end_x - 4 * math.cos(angle - 0.4)
                h1_y = end_y - 4 * math.sin(angle - 0.4)
                h2_x = end_x - 4 * math.cos(angle + 0.4)
                h2_y = end_y - 4 * math.sin(angle + 0.4)
                pygame.draw.line(arrow_surface, color, (end_x, end_y), (h1_x, h1_y), 1)
                pygame.draw.line(arrow_surface, color, (end_x, end_y), (h2_x, h2_y), 1)

        surface.blit(arrow_surface, rect.topleft)
