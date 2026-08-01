from typing import Optional, Dict, Any
import pygame
from simulation.state import PendulumState, energy


class UIRenderer:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.font = pygame.font.SysFont("Consolas", 15)
        self.bold_font = pygame.font.SysFont("Verdana", 16, bold=True)
        self.large_font = pygame.font.SysFont("Verdana", 28, bold=True)

    def draw_status_bar(
        self,
        surface: pygame.Surface,
        state: PendulumState,
        selected_torque: float,
        pulse_count: int,
        pulse_budget: Optional[int],
        target_description: str,
        is_executing: bool,
    ):
        """Draws the main bottom status bar HUD."""
        pygame.draw.rect(surface, (10, 14, 22), self.rect)
        pygame.draw.line(
            surface,
            (45, 60, 90),
            (self.rect.left, self.rect.top),
            (self.rect.right, self.rect.top),
            2,
        )

        current_energy = energy(state)

        # 1. Energy readout
        e_color = (235, 180, 50) if abs(current_energy - 2.0) < 0.1 else (180, 220, 255)
        lbl_energy = self.font.render(
            f"Energy: {current_energy:.2f}",
            True,
            e_color,
        )
        surface.blit(lbl_energy, (self.rect.left + 20, self.rect.top + 15))

        # 2. Selected Pulse Action
        action_names = {-0.35: "LEFT (←/A)", 0.0: "COAST (↓/S)", 0.35: "RIGHT (→/D)"}
        action_str = action_names.get(round(selected_torque, 2), "COAST")

        status_prefix = "EXECUTING..." if is_executing else "SELECTED:"
        pulse_color = (80, 220, 120) if selected_torque > 0 else (
            (240, 80, 80) if selected_torque < 0 else (220, 220, 100)
        )

        lbl_pulse = self.bold_font.render(
            f"Pulse {status_prefix} [{action_str}]",
            True,
            pulse_color,
        )
        surface.blit(lbl_pulse, (self.rect.left + 220, self.rect.top + 14))

        # 3. Pulse Budget / Count
        budget_str = f"{pulse_count}" if pulse_budget is None else f"{pulse_count} / {pulse_budget}"
        lbl_count = self.font.render(
            f"Pulses: {budget_str}",
            True,
            (180, 200, 230),
        )
        surface.blit(lbl_count, (self.rect.left + 540, self.rect.top + 15))

        # 4. Target / Objective
        lbl_target = self.font.render(
            f"Target: {target_description}",
            True,
            (120, 220, 200),
        )
        surface.blit(lbl_target, (self.rect.left + 720, self.rect.top + 15))

    def draw_instructions(self, surface: pygame.Surface, screen_width: int):
        """Draws keybindings help bar at top/bottom."""
        controls_txt = "[←/A] Left Pulse  [↓/S] Coast  [→/D] Right Pulse  [Space/Enter] Commit  [R] Restart  [Tab] Vectors  [F1] Debug"
        lbl = self.font.render(controls_txt, True, (130, 150, 180))
        lbl_rect = lbl.get_rect(center=(screen_width // 2, self.rect.top + 45))
        surface.blit(lbl, lbl_rect)

    def draw_overlay_message(
        self,
        surface: pygame.Surface,
        title: str,
        subtitle: str,
        is_success: bool,
    ):
        """Draws end-of-chamber popup overlay (Success or Failure)."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 180))

        color = (80, 240, 140) if is_success else (255, 90, 90)

        # Title text
        txt_title = self.large_font.render(title, True, color)
        rect_title = txt_title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 25))

        # Subtitle text
        txt_sub = self.bold_font.render(subtitle, True, (220, 230, 245))
        rect_sub = txt_sub.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 25))

        overlay.blit(txt_title, rect_title)
        overlay.blit(txt_sub, rect_sub)

        surface.blit(overlay, (0, 0))
