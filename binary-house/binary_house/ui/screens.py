import pygame
from binary_house.game.state import GameState
from binary_house.ui.fiction import FictionMapper

COLOR_OVERLAY_BG = (10, 12, 18, 220)
COLOR_TEXT_BRIGHT = (245, 245, 250)
COLOR_TEXT_MUTED = (160, 170, 190)
COLOR_ALERT_RED = (255, 80, 100)
COLOR_GOLD_ACCENT = (255, 190, 75)

class ScreenOverlay:
    """End-of-game overlay renderer for Captured, Escaped, and Won states."""
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        pygame.font.init()
        self.title_font = pygame.font.SysFont("Trebuchet MS", 28, bold=True)
        self.subtitle_font = pygame.font.SysFont("Trebuchet MS", 18)
        self.body_font = pygame.font.SysFont("Consolas", 15)

    def render(self, state: GameState, mapper: FictionMapper) -> list[tuple[pygame.Rect, str]]:
        """Render modal overlay based on state.phase ('captured' or 'won'). Returns clickable rects."""
        if state.phase not in ("captured", "won"):
            return []

        w, h = self.surface.get_width(), self.surface.get_height()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 230))
        self.surface.blit(overlay, (0, 0))

        dialog_rect = pygame.Rect(w // 2 - 250, h // 2 - 140, 500, 280)
        pygame.draw.rect(self.surface, (22, 26, 36), dialog_rect, border_radius=12)
        
        border_color = COLOR_ALERT_RED if state.phase == "captured" else COLOR_GOLD_ACCENT
        pygame.draw.rect(self.surface, border_color, dialog_rect, width=2, border_radius=12)

        buttons = []
        if state.phase == "captured":
            t_txt = self.title_font.render("CAPTURED BY THE CARETAKER", True, COLOR_ALERT_RED)
            self.surface.blit(t_txt, (dialog_rect.x + 30, dialog_rect.y + 30))

            recognized_traits = mapper.caretaker_recognition_str(state.caretaker, state.player_address)
            msg1 = f"The Caretaker recognized your lineage."
            msg2 = f"{recognized_traits}"
            
            s1 = self.subtitle_font.render(msg1, True, COLOR_TEXT_BRIGHT)
            s2 = self.body_font.render(msg2, True, COLOR_ALERT_RED)
            self.surface.blit(s1, (dialog_rect.x + 30, dialog_rect.y + 80))
            self.surface.blit(s2, (dialog_rect.x + 30, dialog_rect.y + 110))

            # Restart Button
            btn_rect = pygame.Rect(dialog_rect.x + 150, dialog_rect.y + 200, 200, 44)
            pygame.draw.rect(self.surface, (45, 55, 75), btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, COLOR_ALERT_RED, btn_rect, width=1, border_radius=8)
            btn_txt = self.subtitle_font.render("RESTART (R)", True, COLOR_TEXT_BRIGHT)
            self.surface.blit(btn_txt, (btn_rect.x + 45, btn_rect.y + 10))
            buttons.append((btn_rect, "restart"))

        elif state.phase == "won":
            t_txt = self.title_font.render("ESCAPED THE BINARY HOUSE!", True, COLOR_GOLD_ACCENT)
            self.surface.blit(t_txt, (dialog_rect.x + 30, dialog_rect.y + 30))

            msg1 = f"You retrieved all {len(state.seals_collected)} seals and reached the Exit Wing!"
            msg2 = f"Completed in {state.turn} turns."
            
            s1 = self.subtitle_font.render(msg1, True, COLOR_TEXT_BRIGHT)
            s2 = self.body_font.render(msg2, True, COLOR_GOLD_ACCENT)
            self.surface.blit(s1, (dialog_rect.x + 30, dialog_rect.y + 80))
            self.surface.blit(s2, (dialog_rect.x + 30, dialog_rect.y + 115))

            # Replay Button
            btn_rect = pygame.Rect(dialog_rect.x + 150, dialog_rect.y + 200, 200, 44)
            pygame.draw.rect(self.surface, (45, 55, 75), btn_rect, border_radius=8)
            pygame.draw.rect(self.surface, COLOR_GOLD_ACCENT, btn_rect, width=1, border_radius=8)
            btn_txt = self.subtitle_font.render("PLAY AGAIN (R)", True, COLOR_TEXT_BRIGHT)
            self.surface.blit(btn_txt, (btn_rect.x + 35, btn_rect.y + 10))
            buttons.append((btn_rect, "restart"))

        return buttons
