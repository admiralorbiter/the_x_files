import pygame
from binary_house.game.state import GameState
from binary_house.ui.diegetic_renderer import DiegeticRenderer
from binary_house.ui.debug_renderer import DebugRenderer
from binary_house.ui.fiction import FictionMapper

class Renderer:
    """Unified Renderer supporting Diegetic View (default), Archivist View (F1), and Debug View (F2)."""
    def __init__(self, surface: pygame.Surface, view_mode: str = "diegetic"):
        self.surface = surface
        self.view_mode = view_mode
        self.diegetic_renderer = DiegeticRenderer(surface)
        self.debug_renderer = DebugRenderer(surface)

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

    def render(self, state: GameState, hovered_digit: int | None = None) -> list[tuple[pygame.Rect, int]]:
        mapper = FictionMapper(state.world.depth)

        if self.view_mode == "debug":
            return self.debug_renderer.render(state, hovered_digit=hovered_digit)
        else:
            # Diegetic or Archivist view
            return self.diegetic_renderer.render(state, hovered_digit=hovered_digit, mapper=mapper)
