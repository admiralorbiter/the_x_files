import pygame
from binary_house.core.address import Address

# Palette constants for dark diegetic aesthetic
COLOR_WOODEN_BG = (35, 28, 22)
COLOR_STONE_BG = (22, 28, 35)
COLOR_MOON_LIGHT = (140, 170, 210)
COLOR_SUN_LIGHT = (230, 190, 120)
COLOR_CANDLE_ACCENT = (255, 180, 70)
COLOR_BELL_ACCENT = (180, 140, 255)
COLOR_EYE_HIGHLIGHT = (255, 100, 100)
COLOR_MOTH_HIGHLIGHT = (100, 255, 180)

def draw_lineage_icon(surface: pygame.Surface, rect: pygame.Rect, digit_idx: int, bit_val: int, is_active: bool = True):
    """Draw custom geometric lineage icons for ribbon (tree/tower, moon/sun, candle/bell, eye/moth)."""
    cx, cy = rect.centerx, rect.centery
    color = (240, 240, 245) if is_active else (100, 110, 125)
    width = 2

    if digit_idx == 0:  # Foundation: Tree (0) vs Tower (1)
        if bit_val == 0:
            # Tree (triangle + trunk)
            pygame.draw.polygon(surface, color, [(cx, cy - 10), (cx - 10, cy + 4), (cx + 10, cy + 4)], width=width)
            pygame.draw.line(surface, color, (cx, cy + 4), (cx, cy + 10), width=3)
        else:
            # Tower (rectangle + battlements)
            pygame.draw.rect(surface, color, (cx - 7, cy - 8, 14, 18), width=width)
            pygame.draw.line(surface, color, (cx - 7, cy - 8), (cx - 7, cy - 12), width=2)
            pygame.draw.line(surface, color, (cx + 7, cy - 8), (cx + 7, cy - 12), width=2)

    elif digit_idx == 1:  # Wing: Moon (0) vs Sun (1)
        if bit_val == 0:
            # Crescent Moon
            pygame.draw.circle(surface, color, (cx - 2, cy), 10, width=width)
            pygame.draw.circle(surface, (28, 32, 44), (cx + 3, cy - 2), 9)
        else:
            # Sun
            pygame.draw.circle(surface, color, (cx, cy), 6, width=width)
            for dx, dy in [(-10,0),(10,0),(0,-10),(0,10),(-7,-7),(7,7),(-7,7),(7,-7)]:
                pygame.draw.line(surface, color, (cx + dx//2, cy + dy//2), (cx + dx, cy + dy), width=1)

    elif digit_idx == 2:  # Household: Candle (0) vs Bell (1)
        if bit_val == 0:
            # Candle (stem + flame)
            pygame.draw.rect(surface, color, (cx - 3, cy - 2, 6, 12), width=width)
            pygame.draw.ellipse(surface, COLOR_CANDLE_ACCENT, (cx - 3, cy - 10, 6, 8))
        else:
            # Bell
            pygame.draw.arc(surface, color, (cx - 8, cy - 8, 16, 16), 0, 3.14, width=width)
            pygame.draw.line(surface, color, (cx - 10, cy), (cx + 10, cy), width=width)
            pygame.draw.circle(surface, color, (cx, cy + 4), 2)

    elif digit_idx == 3:  # Memory: Eye (0) vs Moth (1)
        if bit_val == 0:
            # Eye
            pygame.draw.ellipse(surface, color, (cx - 10, cy - 6, 20, 12), width=width)
            pygame.draw.circle(surface, COLOR_EYE_HIGHLIGHT, (cx, cy), 3)
        else:
            # Moth / Butterfly wings
            pygame.draw.ellipse(surface, color, (cx - 10, cy - 8, 10, 8), width=width)
            pygame.draw.ellipse(surface, color, (cx + 0, cy - 8, 10, 8), width=width)
            pygame.draw.line(surface, color, (cx, cy - 8), (cx, cy + 8), width=2)


def render_composite_room_art(surface: pygame.Surface, address: Address, rect: pygame.Rect):
    """Render layered procedural room art stack. Each digit controls one visual layer."""
    # 1. Foundation Layer (b0) - Background architecture & palette
    b0 = address.bit(0)
    bg_color = COLOR_WOODEN_BG if b0 == 0 else COLOR_STONE_BG
    pygame.draw.rect(surface, bg_color, rect, border_radius=10)

    # Architectural arches or stone pillars
    for x_off in [rect.x + 30, rect.x + rect.width - 40]:
        if b0 == 0:
            # Wooden beam
            pygame.draw.rect(surface, (60, 48, 38), (x_off, rect.y, 12, rect.height))
        else:
            # Stone pillar
            pygame.draw.rect(surface, (50, 60, 75), (x_off, rect.y, 16, rect.height))

    # 2. Wing Layer (b1) - Window & Lighting
    b1 = address.bit(1)
    light_color = COLOR_MOON_LIGHT if b1 == 0 else COLOR_SUN_LIGHT
    win_x = rect.x + rect.width // 2 - 25
    win_y = rect.y + 20
    
    # Window glow & aperture
    pygame.draw.rect(surface, light_color, (win_x, win_y, 50, 70), border_radius=25 if b1 == 0 else 4)
    pygame.draw.rect(surface, (15, 18, 24), (win_x + 4, win_y + 4, 42, 62), border_radius=20 if b1 == 0 else 2)
    pygame.draw.line(surface, light_color, (win_x + 25, win_y + 4), (win_x + 25, win_y + 66), width=2)
    pygame.draw.line(surface, light_color, (win_x + 4, win_y + 35), (win_x + 46, win_y + 35), width=2)

    # 3. Household Layer (b2) - Furniture silhouettes
    b2 = address.bit(2)
    furn_color = COLOR_CANDLE_ACCENT if b2 == 0 else COLOR_BELL_ACCENT
    table_cx = rect.x + rect.width // 2
    table_cy = rect.y + rect.height - 70

    if b2 == 0:
        # Round table + chairs
        pygame.draw.ellipse(surface, (30, 35, 45), (table_cx - 40, table_cy - 10, 80, 25))
        pygame.draw.ellipse(surface, furn_color, (table_cx - 40, table_cy - 10, 80, 25), width=2)
    else:
        # Desk + bookshelf silhouette
        pygame.draw.rect(surface, (30, 35, 45), (table_cx - 45, table_cy - 15, 90, 30))
        pygame.draw.rect(surface, furn_color, (table_cx - 45, table_cy - 15, 90, 30), width=2)

    # 4. Memory Layer (b3) - Prop anomaly
    b3 = address.bit(3)
    prop_x = table_cx
    prop_y = table_cy - 20

    if b3 == 0:
        # Intact Portrait
        pygame.draw.rect(surface, COLOR_EYE_HIGHLIGHT, (prop_x - 10, prop_y - 20, 20, 25), width=2)
        pygame.draw.circle(surface, COLOR_EYE_HIGHLIGHT, (prop_x, prop_y - 8), 4)
    else:
        # Scratched portrait / anomaly moth
        pygame.draw.rect(surface, COLOR_MOTH_HIGHLIGHT, (prop_x - 10, prop_y - 20, 20, 25), width=2)
        pygame.draw.line(surface, COLOR_MOTH_HIGHLIGHT, (prop_x - 8, prop_y - 18), (prop_x + 8, prop_y - 2), width=2)
