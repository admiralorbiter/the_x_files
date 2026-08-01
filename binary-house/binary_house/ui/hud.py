import pygame
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.core.metric import distance_level
from binary_house.game.state import GameState

# Theme Palette (Rich Dark Glassmorphism)
COLOR_BG = (18, 20, 28)
COLOR_PANEL_BG = (28, 32, 44)
COLOR_ACCENT_NEAREST = (255, 180, 70)  # Bright warm gold for b₀
COLOR_ACCENT_MID = (70, 200, 255)      # Cyan for middle digits
COLOR_ACCENT_DEEP = (180, 100, 255)    # Violet for deep digits
COLOR_TEXT = (230, 235, 245)
COLOR_TEXT_DIM = (120, 130, 150)
COLOR_HIGHLIGHT = (255, 100, 120)

class HUD:
    """HUD renderer for 2-adic navigation: ribbon, neighborhood stack, scale ledger, previews."""
    def __init__(self, font: pygame.font.Font, small_font: pygame.font.Font):
        self.font = font
        self.small_font = small_font

    def render_ribbon(self, surface: pygame.Surface, address: Address, hovered_digit: int | None, rect: pygame.Rect):
        """Render near-first address ribbon with pulsing highlight on target door digit."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        
        # Header label
        header = self.small_font.render("NEAR-FIRST ADDRESS  (b₀ · b₁ · b₂ · b₃ · b₄ · b₅ · b₆ · b₇)", True, COLOR_TEXT_DIM)
        surface.blit(header, (rect.x + 16, rect.y + 8))

        # Digits display
        x_offset = rect.x + 16
        for i in range(address.depth):
            bit_val = address.bit(i)
            is_hovered = (hovered_digit == i)
            
            if is_hovered:
                color = COLOR_HIGHLIGHT
                digit_str = f"[{bit_val}]"
            else:
                if i < 2:
                    color = COLOR_ACCENT_NEAREST
                elif i < 5:
                    color = COLOR_ACCENT_MID
                else:
                    color = COLOR_ACCENT_DEEP
                digit_str = f" {bit_val} "

            txt = self.font.render(digit_str, True, color)
            surface.blit(txt, (x_offset, rect.y + 28))
            x_offset += txt.get_width() + 12

    def render_neighborhood_stack(self, surface: pygame.Surface, state: GameState, rect: pygame.Rect):
        """Render left sidebar neighborhood containment hierarchy stack."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        
        title = self.small_font.render("NEIGHBORHOOD STACK", True, COLOR_TEXT_DIM)
        surface.blit(title, (rect.x + 12, rect.y + 12))

        y = rect.y + 36
        addr = state.player_address
        for depth in range(1, addr.depth + 1):
            prefix_val = addr.prefix(depth)
            ball = Ball(residue=prefix_val, depth=depth, total_depth=addr.depth)
            
            # Format string prefix
            bits_str = "".join(str(addr.bit(i)) for i in range(depth)) + "·" * (addr.depth - depth)
            
            # Check markers
            is_marked = ball in state.chalk_marks
            has_caretaker = state.caretaker.is_detecting(addr) if (state.enable_caretaker and depth == state.caretaker.detection_depth) else False
            has_exit = state.world.exit_ball.relationship(ball, state.world.exit_ball) in ("equal", "nested")

            status = ""
            color = COLOR_TEXT
            if has_caretaker:
                status += " ⚠️ ENEMY DETECTED"
                color = COLOR_HIGHLIGHT
            if has_exit:
                status += " 🚪 EXIT BALL"
                color = COLOR_ACCENT_NEAREST
            if is_marked:
                status += " ✏️ CHALKED"

            line_str = f"d={depth}: {bits_str} ({ball.size()} rooms){status}"
            txt = self.small_font.render(line_str, True, color)
            surface.blit(txt, (rect.x + 12, y))
            y += 22

    def render_scale_ledger(self, surface: pygame.Surface, state: GameState, rect: pygame.Rect):
        """Render right sidebar scale ledger (distance rings, NO angular positions)."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        
        title = self.small_font.render("SCALE LEDGER (Distances)", True, COLOR_TEXT_DIM)
        surface.blit(title, (rect.x + 12, rect.y + 12))

        y = rect.y + 36
        # Group known entities by distance level
        p_addr = state.player_address
        
        # Caretaker distance
        if state.enable_caretaker:
            c_dist = distance_level(p_addr, state.caretaker.address)
            c_str = f"Caretaker: distance 2^-{c_dist}" if c_dist is not None else "Caretaker: SAME ROOM!"
            txt = self.small_font.render(c_str, True, COLOR_HIGHLIGHT)
            surface.blit(txt, (rect.x + 12, y))
            y += 24

        # Seals distance
        for idx, s_addr in enumerate(state.world.seal_locations):
            if idx not in state.seals_collected:
                s_dist = distance_level(p_addr, s_addr)
                s_str = f"Seal #{idx+1}: distance 2^-{s_dist}" if s_dist is not None else f"Seal #{idx+1}: HERE!"
                txt = self.small_font.render(s_str, True, COLOR_ACCENT_MID)
                surface.blit(txt, (rect.x + 12, y))
                y += 24

        # Exit distance
        if state.world.exit_ball.contains(p_addr):
            txt = self.small_font.render("Exit: INSIDE EXIT BALL!", True, COLOR_ACCENT_NEAREST)
            surface.blit(txt, (rect.x + 12, y))
        else:
            txt = self.small_font.render(f"Exit: target depth-{state.world.exit_ball.depth} ball", True, COLOR_TEXT_DIM)
            surface.blit(txt, (rect.x + 12, y))
