import pygame
from binary_house.game.state import GameState
from binary_house.ui.diegetic_renderer import DiegeticRenderer
from binary_house.ui.debug_renderer import DebugRenderer
from binary_house.ui.fiction import FictionMapper

from binary_house.ui.screens import ScreenOverlay

class Renderer:
    """Unified Renderer supporting Diegetic View (default), Archivist View (F1), and Debug View (F2)."""
    def __init__(self, surface: pygame.Surface, view_mode: str = "diegetic"):
        self.surface = surface
        self.view_mode = view_mode
        self.diegetic_renderer = DiegeticRenderer(surface)
        self.debug_renderer = DebugRenderer(surface)
        self.screen_overlay = ScreenOverlay(surface)

    def toggle_archivist(self):
        if self.view_mode == "archivist":
            self.view_mode = "diegetic"
        else:
            self.view_mode = "archivist"

    def toggle_debug(self):
        if self.view_mode == "debug":
            self.view_mode = "diegetic"
        else:
            self.view_mode = "debug"

    def start_transition(self, from_addr, to_addr, digit_changed: int):
        self.diegetic_renderer.start_transition(from_addr, to_addr, digit_changed)

    def update_transition(self, dt_ms: float):
        self.diegetic_renderer.update_transition(dt_ms)

    def render(self, state: GameState, hovered_digit: int | None = None) -> tuple[list[tuple[pygame.Rect, int]], list[tuple[pygame.Rect, str]]]:
        mapper = FictionMapper(state.world.depth)

        if self.view_mode == "debug":
            door_rects = self.debug_renderer.render(state, hovered_digit=hovered_digit)
            overlay_buttons = self.screen_overlay.render(state, mapper)
            return door_rects, overlay_buttons
        else:
            # Diegetic or Archivist view
            door_rects = self.diegetic_renderer.render(state, hovered_digit=hovered_digit, mapper=mapper)
            overlay_buttons = self.screen_overlay.render(state, mapper)
            return door_rects, overlay_buttons
