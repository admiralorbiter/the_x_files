import math
from dataclasses import dataclass
from typing import Optional, Protocol, Tuple, Any
import pygame
from simulation.state import PendulumState, wrap_theta, energy


@dataclass
class ConstraintResult:
    satisfied: bool = False
    failed: bool = False
    message: str = ""


class PhaseConstraint(Protocol):
    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        ...

    def draw_phase(self, surface: pygame.Surface, phase_view: Any) -> None:
        ...

    def draw_physical(self, surface: pygame.Surface, physical_view: Any) -> None:
        ...


class StateGate:
    """
    Vertical wall in phase space at angle target_theta with passable window [omega_min, omega_max].
    Crossing at wrong speed or wrong direction fails or misses the gate.
    """

    def __init__(
        self,
        target_theta: float,
        omega_min: float,
        omega_max: float,
        name: str = "State Gate",
    ):
        self.target_theta = target_theta
        self.omega_min = omega_min
        self.omega_max = omega_max
        self.name = name

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        # Check angle crossing
        t1 = wrap_theta(previous.theta)
        t2 = wrap_theta(current.theta)

        # Avoid seam jumps
        if abs(t1 - t2) > math.pi:
            return ConstraintResult()

        # Did transition cross target_theta?
        min_t, max_t = min(t1, t2), max(t1, t2)
        if min_t <= self.target_theta <= max_t:
            # Estimate omega at crossing
            avg_omega = 0.5 * (previous.omega + current.omega)
            if self.omega_min <= avg_omega <= self.omega_max:
                return ConstraintResult(
                    satisfied=True,
                    message=f"{self.name} Passed! (ω = {avg_omega:.2f})",
                )
            else:
                return ConstraintResult(
                    failed=True,
                    message=f"{self.name} Missed! Speed {avg_omega:.2f} outside [{self.omega_min:.1f}, {self.omega_max:.1f}]",
                )

        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        # Draw vertical line with open window gap in phase space
        px, py_top = phase_view.to_screen(self.target_theta, phase_view.omega_max)
        _, py_bottom = phase_view.to_screen(self.target_theta, phase_view.omega_min)

        w_min_px, py_w_min = phase_view.to_screen(self.target_theta, self.omega_min)
        w_max_px, py_w_max = phase_view.to_screen(self.target_theta, self.omega_max)

        # Wall above window
        pygame.draw.line(
            surface,
            (220, 70, 70),
            (px, phase_view.rect.top),
            (px, py_w_max),
            3,
        )
        # Wall below window
        pygame.draw.line(
            surface,
            (220, 70, 70),
            (px, py_w_min),
            (px, phase_view.rect.bottom),
            3,
        )
        # Passable window gap
        pygame.draw.line(surface, (80, 240, 140), (px, py_w_max), (px, py_w_min), 4)

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        # Draw physical arc gate at target_theta
        bx, by = physical_view.get_bob_position(self.target_theta)
        pygame.draw.circle(surface, (80, 240, 140), (bx, by), 12, 2)


class SpeedBarrier:
    """
    Horizontal hazard band in phase space: |ω| > max_omega damages mechanism.
    """

    def __init__(self, max_omega: float, name: str = "Speed Barrier"):
        self.max_omega = max_omega
        self.name = name

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        if abs(current.omega) > self.max_omega:
            return ConstraintResult(
                failed=True,
                message=f"MECHANISM FAILURE! Speed |ω|={abs(current.omega):.2f} exceeded limit {self.max_omega:.1f}",
            )
        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        # Render shaded hazard zones at top/bottom of phase space
        _, py_top_limit = phase_view.to_screen(0, self.max_omega)
        _, py_bot_limit = phase_view.to_screen(0, -self.max_omega)

        # Top hazard
        top_rect = pygame.Rect(
            phase_view.rect.left,
            phase_view.rect.top,
            phase_view.rect.width,
            max(0, py_top_limit - phase_view.rect.top),
        )
        # Bottom hazard
        bot_rect = pygame.Rect(
            phase_view.rect.left,
            py_bot_limit,
            phase_view.rect.width,
            max(0, phase_view.rect.bottom - py_bot_limit),
        )

        haz_surf = pygame.Surface(phase_view.rect.size, pygame.SRCALPHA)
        if top_rect.height > 0:
            pygame.draw.rect(
                haz_surf,
                (255, 40, 40, 60),
                (0, 0, top_rect.width, top_rect.height),
            )
        if bot_rect.height > 0:
            py_rel = py_bot_limit - phase_view.rect.top
            pygame.draw.rect(
                haz_surf,
                (255, 40, 40, 60),
                (0, py_rel, bot_rect.width, haz_surf.get_height() - py_rel),
            )

        surface.blit(haz_surf, phase_view.rect.topleft)

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        pass


class DirectionalGate:
    """
    Gate requiring angle crossing with specific velocity direction (ω > 0 or ω < 0).
    """

    def __init__(self, target_theta: float, require_positive_omega: bool = True):
        self.target_theta = target_theta
        self.require_positive_omega = require_positive_omega

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        t1 = wrap_theta(previous.theta)
        t2 = wrap_theta(current.theta)
        if abs(t1 - t2) > math.pi:
            return ConstraintResult()

        if min(t1, t2) <= self.target_theta <= max(t1, t2):
            avg_omega = 0.5 * (previous.omega + current.omega)
            if self.require_positive_omega and avg_omega > 0:
                return ConstraintResult(satisfied=True, message="Directional Gate Passed (Clockwise)!")
            elif not self.require_positive_omega and avg_omega < 0:
                return ConstraintResult(satisfied=True, message="Directional Gate Passed (Counterclockwise)!")
            else:
                return ConstraintResult(failed=True, message="Wrong Direction through Gate!")

        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        px, py_zero = phase_view.to_screen(self.target_theta, 0.0)
        color = (0, 220, 255)
        if self.require_positive_omega:
            _, py_top = phase_view.to_screen(self.target_theta, phase_view.omega_max)
            pygame.draw.line(surface, color, (px, py_zero), (px, py_top), 3)
        else:
            _, py_bot = phase_view.to_screen(self.target_theta, phase_view.omega_min)
            pygame.draw.line(surface, color, (px, py_zero), (px, py_bot), 3)

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        bx, by = physical_view.get_bob_position(self.target_theta)
        pygame.draw.circle(surface, (0, 220, 255), (bx, by), 10, 2)


class EnergyLock:
    """
    Lock that activates only if state energy is within [min_energy, max_energy].
    """

    def __init__(self, min_energy: float, max_energy: float):
        self.min_energy = min_energy
        self.max_energy = max_energy

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        e = energy(current)
        if self.min_energy <= e <= self.max_energy:
            return ConstraintResult(satisfied=True, message=f"Energy Lock Unlocked (E = {e:.2f})!")
        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        pass

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        pass


class RotationKey:
    """
    Requires completing at least one full 360-degree rotation (unwrapped |Δθ| >= 2π).
    """

    def __init__(self, start_theta: float, name: str = "Rotation Key"):
        self.start_theta = start_theta
        self.name = name

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        delta = abs(current.theta - self.start_theta)
        if delta >= 2.0 * math.pi:
            return ConstraintResult(
                satisfied=True,
                message=f"{self.name} Collected! (Rotated 360°)",
            )
        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        pass

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        pass


class UprightDock:
    """
    Target region near upright position (θ = ±π, ω = 0).
    Requires low velocity to successfully dock.
    """

    def __init__(
        self,
        theta_tol: float = 0.12,
        omega_tol: float = 0.18,
        name: str = "Upright Dock",
    ):
        self.theta_tol = theta_tol
        self.omega_tol = omega_tol
        self.name = name

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        wrapped_dist = abs(wrap_theta(current.theta - math.pi))
        if wrapped_dist < self.theta_tol and abs(current.omega) < self.omega_tol:
            return ConstraintResult(
                satisfied=True,
                message=f"{self.name} DOCKED! (Top position captured cleanly)",
            )
        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        px, py = phase_view.to_screen(math.pi, 0.0)
        px_neg, _ = phase_view.to_screen(-math.pi, 0.0)

        # Upright dock exists at both cylinder seams (θ = +π and θ = -π)
        for center_x in [px, px_neg]:
            rect = pygame.Rect(center_x - 12, py - 12, 24, 24)
            pygame.draw.rect(surface, (80, 240, 140), rect, 2)
            pygame.draw.circle(surface, (80, 240, 140), (center_x, py), 4)

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        bx, by = physical_view.get_bob_position(math.pi)
        pygame.draw.circle(surface, (80, 240, 140), (bx, by), 20, 2)


class DownwardDock:
    """
    Target region near downward equilibrium (θ = 0, ω = 0).
    """

    def __init__(
        self,
        theta_tol: float = 0.12,
        omega_tol: float = 0.15,
        name: str = "Downward Dock",
    ):
        self.theta_tol = theta_tol
        self.omega_tol = omega_tol
        self.name = name

    def check_transition(
        self,
        previous: PendulumState,
        current: PendulumState,
    ) -> ConstraintResult:
        if abs(wrap_theta(current.theta)) < self.theta_tol and abs(current.omega) < self.omega_tol:
            return ConstraintResult(
                satisfied=True,
                message=f"{self.name} DOCKED! (Bottom position captured cleanly)",
            )
        return ConstraintResult()

    def draw_phase(self, surface: pygame.Surface, phase_view: Any):
        px, py = phase_view.to_screen(0.0, 0.0)
        rect = pygame.Rect(px - 14, py - 14, 28, 28)
        pygame.draw.rect(surface, (80, 240, 140), rect, 2)
        pygame.draw.circle(surface, (80, 240, 140), (px, py), 4)

    def draw_physical(self, surface: pygame.Surface, physical_view: Any):
        bx, by = physical_view.get_bob_position(0.0)
        pygame.draw.circle(surface, (80, 240, 140), (bx, by), 20, 2)
