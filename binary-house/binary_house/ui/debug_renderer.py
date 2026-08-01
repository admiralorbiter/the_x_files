import pygame
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction
from binary_house.ui.hud import HUD, COLOR_BG, COLOR_PANEL_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_ACCENT_NEAREST, COLOR_ACCENT_MID, COLOR_HIGHLIGHT
from binary_house.ui.audio import AudioSynthesizer

# Shape families for abstract room card rendering
SHAPE_FAMILIES = ["Circle", "Square", "Diamond", "Triangle", "Hexagon", "Star", "Octagon", "Cross"]

class DebugRenderer:
    """F2 Mathematical Debug View renderer (exact addresses, distance exponents, bit operations)."""
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 18, bold=True)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        self.title_font = pygame.font.SysFont("Trebuchet MS", 22, bold=True)
        self.hud = HUD(self.font, self.small_font)
        self.audio = AudioSynthesizer()
        self.last_played_addr = None

    def draw_room_card(self, surface: pygame.Surface, state: GameState, rect: pygame.Rect) -> list[tuple[pygame.Rect, int]]:
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=12)
        
        current_room = state.world.rooms[state.player_address.value]
        style = current_room.style

        b0, b1, b2 = state.player_address.bit(0), state.player_address.bit(1), state.player_address.bit(2)
        if self.last_played_addr != state.player_address.value:
            self.audio.play_room_motif(b0, b1, b2)
            self.last_played_addr = state.player_address.value

        shape_name = SHAPE_FAMILIES[style.architecture_family % len(SHAPE_FAMILIES)]
        hue_idx = style.palette_index
        pattern_id = style.floor_pattern

        title_txt = self.title_font.render(f"ROOM [Address: {state.player_address.near_first_str()}]", True, COLOR_TEXT)
        surface.blit(title_txt, (rect.x + 20, rect.y + 16))

        traits_str = f"Style: {shape_name} Structure | Palette #{hue_idx} | Pattern #{pattern_id}"
        traits_txt = self.small_font.render(traits_str, True, COLOR_ACCENT_MID)
        surface.blit(traits_txt, (rect.x + 20, rect.y + 44))

        center_x = rect.x + rect.width // 2
        center_y = rect.y + 120
        pygame.draw.circle(surface, COLOR_ACCENT_NEAREST if b0 == 0 else COLOR_ACCENT_MID, (center_x, center_y), 45, width=4)
        if b1 == 1:
            pygame.draw.rect(surface, COLOR_ACCENT_MID, (center_x - 20, center_y - 20, 40, 40), width=3)
        if b2 == 1:
            pygame.draw.circle(surface, COLOR_HIGHLIGHT, (center_x, center_y), 15)

        contents_y = rect.y + 190
        if current_room.contains_seal is not None:
            txt = self.font.render(f"🌟 CONTAINS SEAL #{current_room.contains_seal + 1}", True, COLOR_ACCENT_NEAREST)
            surface.blit(txt, (rect.x + 20, contents_y))
            contents_y += 26
        if current_room.contains_resource:
            txt = self.font.render(f"📦 RESOURCE: {current_room.contains_resource.upper()}", True, COLOR_ACCENT_MID)
            surface.blit(txt, (rect.x + 20, contents_y))
            contents_y += 26

        doors_header = self.small_font.render("AVAILABLE DOORS (F2 DEBUG VIEW):", True, COLOR_TEXT_DIM)
        surface.blit(doors_header, (rect.x + 20, rect.y + 260))

        door_rects = []
        door_y = rect.y + 285
        for door in current_room.doors:
            scale_idx = door.index
            target_addr = door.apply(state.player_address)
            scale_type = "STRUCTURAL (Loud)" if scale_idx == 0 else ("LOCAL" if scale_idx < 3 else "DEEP (Quiet)")
            
            d_rect = pygame.Rect(rect.x + 20, door_y, rect.width - 40, 36)
            pygame.draw.rect(surface, (40, 48, 66), d_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_ACCENT_MID, d_rect, width=1, border_radius=6)

            door_text = f"Door digit {scale_idx} [{scale_type}] -> {target_addr.near_first_str()}"
            txt = self.font.render(door_text, True, COLOR_TEXT)
            surface.blit(txt, (d_rect.x + 12, d_rect.y + 8))
            
            door_rects.append((d_rect, scale_idx))
            door_y += 44

        return door_rects

    def render(self, state: GameState, hovered_digit: int | None = None) -> list[tuple[pygame.Rect, int]]:
        self.surface.fill(COLOR_BG)
        
        ribbon_rect = pygame.Rect(16, 16, self.surface.get_width() - 32, 64)
        self.hud.render_ribbon(self.surface, state.player_address, hovered_digit, ribbon_rect)

        sidebar_left_rect = pygame.Rect(16, 92, 280, 480)
        self.hud.render_neighborhood_stack(self.surface, state, sidebar_left_rect)

        center_rect = pygame.Rect(308, 92, 480, 480)
        door_rects = self.draw_room_card(self.surface, state, center_rect)

        sidebar_right_rect = pygame.Rect(800, 92, 268, 480)
        self.hud.render_scale_ledger(self.surface, state, sidebar_right_rect)

        log_rect = pygame.Rect(16, 584, self.surface.get_width() - 32, 48)
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, log_rect, border_radius=8)
        if state.event_log:
            last_event = state.event_log[-1]
            txt = self.small_font.render(f"Turn {last_event.turn}: {last_event.description}", True, COLOR_ACCENT_NEAREST if state.phase == "won" else COLOR_TEXT)
            self.surface.blit(txt, (log_rect.x + 16, log_rect.y + 16))
        else:
            txt = self.small_font.render("[F2 DEBUG] Shared low-order digits = closeness!", True, COLOR_TEXT_DIM)
            self.surface.blit(txt, (log_rect.x + 16, log_rect.y + 16))

        pygame.display.flip()
        return door_rects
