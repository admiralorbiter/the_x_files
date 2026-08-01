import pygame
from binary_house.game.state import GameState
from binary_house.game.player import MoveAction
from binary_house.core.door import ToggleDigit
from binary_house.core.ball import Ball
from binary_house.core.metric import distance_level
from binary_house.ui.fiction import FictionMapper, DoorPreview
from binary_house.ui.assets import render_composite_room_art, draw_lineage_icon
from binary_house.ui.audio import AudioSynthesizer
from binary_house.ui.transitions import Transition

# Diegetic Theme Palette
COLOR_DIEGETIC_BG = (14, 16, 22)
COLOR_PANEL_BG = (24, 28, 38)
COLOR_PANEL_BORDER = (45, 52, 70)
COLOR_TEXT_BRIGHT = (240, 242, 248)
COLOR_TEXT_NORMAL = (190, 198, 215)
COLOR_TEXT_MUTED = (110, 120, 140)
COLOR_ALERT_RED = (255, 90, 110)
COLOR_GOLD_ACCENT = (255, 185, 75)
COLOR_CYAN_ACCENT = (80, 200, 240)

class DiegeticRenderer:
    """Player-facing diegetic view compositor for The House That Remembers."""
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        pygame.font.init()
        self.title_font = pygame.font.SysFont("Trebuchet MS", 20, bold=True)
        self.normal_font = pygame.font.SysFont("Consolas", 15)
        self.small_font = pygame.font.SysFont("Consolas", 13)
        self.audio = AudioSynthesizer()
        self.current_transition: Transition | None = None
        self.last_played_addr: int | None = None

    def start_transition(self, from_addr, to_addr, digit_changed: int):
        self.current_transition = Transition.create(from_addr, to_addr, digit_changed)

    def update_transition(self, dt_ms: float):
        if self.current_transition:
            finished = self.current_transition.update(dt_ms)
            if finished:
                self.current_transition = None

    def render_lineage_ribbon(self, surface: pygame.Surface, state: GameState, hovered_digit: int | None, mapper: FictionMapper, rect: pygame.Rect):
        """Render top Lineage Ribbon with custom geometric icons and Seal Counter."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=8)

        # Mode hint & title
        seals_count_str = f"SEALS COLLECTED: 🌟 {len(state.seals_collected)} / {len(state.world.seal_locations)}"
        if len(state.seals_collected) >= len(state.world.seal_locations):
            seals_count_str += " (READY TO ESCAPE!)"
            
        lbl = self.small_font.render(f"HOUSE LINEAGE | {seals_count_str} (F1: Archivist | F2: Math Debug)", True, COLOR_GOLD_ACCENT if len(state.seals_collected) >= len(state.world.seal_locations) else COLOR_TEXT_MUTED)
        surface.blit(lbl, (rect.x + 16, rect.y + 6))

        # Render each layer box
        x_offset = rect.x + 16
        box_width = 160
        addr = state.player_address

        h = state.caretaker.detection_depth if (state.enable_caretaker and state.caretaker) else 0

        for i in range(min(4, addr.depth)):
            layer_info = mapper.layer(i)
            bit_val = addr.bit(i)
            trait_name = mapper.trait_name(i, bit_val)
            
            is_hovered = (hovered_digit == i)
            is_recognized_by_caretaker = (state.enable_caretaker and i < h and state.phase == "detected")

            box_rect = pygame.Rect(x_offset, rect.y + 24, box_width, 36)
            
            # Border & glow
            if is_recognized_by_caretaker:
                pygame.draw.rect(surface, (60, 20, 30), box_rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_ALERT_RED, box_rect, width=2, border_radius=6)
            elif is_hovered:
                pygame.draw.rect(surface, (40, 50, 70), box_rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_GOLD_ACCENT, box_rect, width=2, border_radius=6)
            else:
                pygame.draw.rect(surface, (30, 36, 48), box_rect, border_radius=6)

            # Icon
            icon_rect = pygame.Rect(box_rect.x + 8, box_rect.y + 8, 20, 20)
            draw_lineage_icon(surface, icon_rect, i, bit_val, is_active=not is_hovered)

            # Trait text
            txt_color = COLOR_ALERT_RED if is_recognized_by_caretaker else (COLOR_GOLD_ACCENT if is_hovered else COLOR_TEXT_BRIGHT)
            txt = self.small_font.render(f"{layer_info.name}: {trait_name}", True, txt_color)
            surface.blit(txt, (box_rect.x + 32, box_rect.y + 10))

            x_offset += box_width + 12

    def render_house_memory(self, surface: pygame.Surface, state: GameState, mapper: FictionMapper, rect: pygame.Rect):
        """Render left sidebar House Memory (nested frames)."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=8)

        title = self.small_font.render("HOUSE MEMORY", True, COLOR_TEXT_MUTED)
        surface.blit(title, (rect.x + 12, rect.y + 10))

        addr = state.player_address
        pad = 8
        frame_rect = pygame.Rect(rect.x + pad, rect.y + 32, rect.width - 2 * pad, rect.height - 42)

        # Draw nested boxes from depth 1 to depth 4
        for d in range(1, min(5, addr.depth + 1)):
            prefix_val = addr.prefix(d)
            ball = Ball(residue=prefix_val, depth=d, total_depth=addr.depth)
            
            # Label
            layer_info = mapper.layer(d - 1)
            trait_name = mapper.trait_name(d - 1, addr.bit(d - 1))
            
            has_caretaker = (state.enable_caretaker and state.caretaker.is_detecting(addr) and d == state.caretaker.detection_depth)
            has_exit = Ball.relationship(ball, state.world.exit_ball) in ("equal", "nested")

            border_color = COLOR_ALERT_RED if has_caretaker else (COLOR_GOLD_ACCENT if has_exit else (60, 70, 90))
            pygame.draw.rect(surface, border_color, frame_rect, width=1, border_radius=4)

            lbl_str = f"Depth {d}: {trait_name} ({ball.size()} rooms)"
            if has_caretaker:
                lbl_str += " ⚠️ RECOGNIZED"
            elif has_exit:
                lbl_str += " 🚪 EXIT WING"

            txt = self.small_font.render(lbl_str, True, COLOR_ALERT_RED if has_caretaker else COLOR_TEXT_NORMAL)
            surface.blit(txt, (frame_rect.x + 6, frame_rect.y + 4))

            frame_rect = pygame.Rect(frame_rect.x + 6, frame_rect.y + 24, frame_rect.width - 12, frame_rect.height - 30)

    def render_echoes_ledger(self, surface: pygame.Surface, state: GameState, mapper: FictionMapper, rect: pygame.Rect):
        """Render right sidebar Echoes panel."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=8)

        title = self.small_font.render("ECHOES IN THE HOUSE", True, COLOR_TEXT_MUTED)
        surface.blit(title, (rect.x + 12, rect.y + 10))

        y = rect.y + 34
        p_addr = state.player_address

        # Active Sound Regions echo
        if state.sound_regions:
            for s in state.sound_regions:
                sound_wing = mapper.wing_name(s.ball)
                fade_str = " (fading)" if s.age > 1 else ""
                txt = self.small_font.render(f"👂 Noise in {sound_wing}{fade_str}", True, COLOR_GOLD_ACCENT)
                surface.blit(txt, (rect.x + 12, y))
                y += 22

        # Caretaker echo
        if state.enable_caretaker:
            c_str = mapper.caretaker_recognition_str(state.caretaker, p_addr)
            if state.phase == "detected":
                txt = self.small_font.render(f"⚠️ {c_str}", True, COLOR_ALERT_RED)
            else:
                txt = self.small_font.render(f"👂 Caretaker distant", True, COLOR_TEXT_MUTED)
            surface.blit(txt, (rect.x + 12, y))
            y += 24

        # Seals echoes (always show all 3 seals)
        for idx, s_addr in enumerate(state.world.seal_locations):
            if idx in state.seals_collected:
                txt = self.small_font.render(f"🌟 Seal #{idx+1}: ✓ COLLECTED", True, COLOR_GOLD_ACCENT)
            else:
                level = distance_level(p_addr, s_addr)
                echo_text = mapper.echo_str(level, state.world.depth)
                txt = self.small_font.render(f"🌟 Seal #{idx+1}: {echo_text}", True, COLOR_CYAN_ACCENT)
            surface.blit(txt, (rect.x + 12, y))
            y += 24

        # Exit echo
        if state.world.exit_ball.contains(p_addr):
            if len(state.seals_collected) >= len(state.world.seal_locations):
                txt = self.small_font.render("🚪 Way Out: INSIDE EXIT WING! (ESCAPED)", True, COLOR_GOLD_ACCENT)
            else:
                needed = len(state.world.seal_locations) - len(state.seals_collected)
                txt = self.small_font.render(f"🚪 Way Out: HERE (Need {needed} more seals)", True, COLOR_CYAN_ACCENT)
            surface.blit(txt, (rect.x + 12, y))
        else:
            txt = self.small_font.render("🚪 Way Out: In Moon Wing", True, COLOR_TEXT_MUTED)
            surface.blit(txt, (rect.x + 12, y))

    def render_room_panel(
        self,
        surface: pygame.Surface,
        state: GameState,
        mapper: FictionMapper,
        rect: pygame.Rect,
    ) -> list[tuple[pygame.Rect, int]]:
        """Render central illustrated room panel with doors."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=10)

        current_room = state.world.rooms[state.player_address.value]

        # Audio motif playback
        b0, b1, b2 = state.player_address.bit(0), state.player_address.bit(1), state.player_address.bit(2)
        if self.last_played_addr != state.player_address.value:
            self.audio.play_room_motif(b0, b1, b2)
            self.last_played_addr = state.player_address.value

        # Room art viewport
        art_rect = pygame.Rect(rect.x + 16, rect.y + 16, rect.width - 32, 220)
        if self.current_transition:
            self.current_transition.render(surface, art_rect)
        else:
            render_composite_room_art(surface, state.player_address, art_rect)

        # Room title
        lineage_title = mapper.lineage_str(state.player_address)
        title_txt = self.title_font.render(f"ROOM: {lineage_title}", True, COLOR_TEXT_BRIGHT)
        surface.blit(title_txt, (rect.x + 16, rect.y + 244))

        # Room items
        item_y = rect.y + 272
        if current_room.contains_seal is not None:
            txt = self.small_font.render(f"🌟 FOUND SEAL #{current_room.contains_seal + 1}", True, COLOR_GOLD_ACCENT)
            surface.blit(txt, (rect.x + 16, item_y))
            item_y += 20
        if current_room.contains_resource:
            txt = self.small_font.render(f"📦 RESOURCE: {current_room.contains_resource.upper()}", True, COLOR_CYAN_ACCENT)
            surface.blit(txt, (rect.x + 16, item_y))
            item_y += 20

        # Doors header
        doors_hdr = self.small_font.render("AVAILABLE PASSAGES:", True, COLOR_TEXT_MUTED)
        surface.blit(doors_hdr, (rect.x + 16, rect.y + 316))

        door_rects = []
        door_y = rect.y + 336
        for door in current_room.doors:
            preview = mapper.door_preview(
                door,
                state.player_address,
                state.caretaker if state.enable_caretaker else None,
                enable_caretaker=state.enable_caretaker,
            )

            d_rect = pygame.Rect(rect.x + 16, door_y, rect.width - 32, 34)
            pygame.draw.rect(surface, (36, 42, 58), d_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_CYAN_ACCENT if door.index > 1 else COLOR_GOLD_ACCENT, d_rect, width=1, border_radius=6)

            door_text = f"[{door.index}] {preview.door_object} ({preview.layer_name}) -> {preview.noise}"
            txt = self.normal_font.render(door_text, True, COLOR_TEXT_BRIGHT)
            surface.blit(txt, (d_rect.x + 10, d_rect.y + 7))

            door_rects.append((d_rect, door.index))
            door_y += 40

        return door_rects

    def render_footer_preview(
        self,
        surface: pygame.Surface,
        state: GameState,
        hovered_digit: int | None,
        mapper: FictionMapper,
        rect: pygame.Rect,
    ):
        """Render bottom preview / post-move flavor sentence bar."""
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=8)

        if hovered_digit is not None:
            door = ToggleDigit(hovered_digit)
            prev = mapper.door_preview(
                door,
                state.player_address,
                state.caretaker if state.enable_caretaker else None,
                enable_caretaker=state.enable_caretaker,
            )

            kept_str = " · ".join(prev.kept_names) if prev.kept_names else "(none)"
            status_color = COLOR_ALERT_RED if prev.caretaker_still_detects else COLOR_GOLD_ACCENT

            msg1 = f"{prev.door_object.upper()}: Keeps {kept_str} | Changes {prev.changed_name} | {prev.noise}"
            msg2 = prev.flavor
            if prev.caretaker_still_detects and state.phase == "detected":
                msg2 += " ⚠️ CARETAKER WILL STILL RECOGNIZE YOU!"

            t1 = self.small_font.render(msg1, True, COLOR_TEXT_BRIGHT)
            t2 = self.small_font.render(msg2, True, status_color)
            surface.blit(t1, (rect.x + 16, rect.y + 8))
            surface.blit(t2, (rect.x + 16, rect.y + 26))

        elif state.event_log:
            last = state.event_log[-1]
            flavor = mapper.post_move_flavor(last.player_before, last.player_after)
            txt = self.small_font.render(f"Turn {last.turn}: {flavor}", True, COLOR_GOLD_ACCENT if state.phase == "won" else COLOR_TEXT_NORMAL)
            surface.blit(txt, (rect.x + 16, rect.y + 14))

        else:
            txt = self.small_font.render("Explore the house. Rooms that share an inheritance resemble each other.", True, COLOR_TEXT_MUTED)
            surface.blit(txt, (rect.x + 16, rect.y + 14))

    def render(self, state: GameState, hovered_digit: int | None = None, mapper: FictionMapper = None) -> list[tuple[pygame.Rect, int]]:
        if mapper is None:
            mapper = FictionMapper(state.world.depth)

        self.surface.fill(COLOR_DIEGETIC_BG)

        # 1. Top Ribbon
        ribbon_rect = pygame.Rect(16, 16, self.surface.get_width() - 32, 68)
        self.render_lineage_ribbon(self.surface, state, hovered_digit, mapper, ribbon_rect)

        # 2. Left House Memory Panel
        memory_rect = pygame.Rect(16, 96, 260, 470)
        self.render_house_memory(self.surface, state, mapper, memory_rect)

        # 3. Central Room Panel
        center_rect = pygame.Rect(288, 96, 500, 470)
        door_rects = self.render_room_panel(self.surface, state, mapper, center_rect)

        # 4. Right Echoes Panel
        echoes_rect = pygame.Rect(800, 96, 268, 470)
        self.render_echoes_ledger(self.surface, state, mapper, echoes_rect)

        # 5. Bottom Preview Footer
        footer_rect = pygame.Rect(16, 578, self.surface.get_width() - 32, 54)
        self.render_footer_preview(self.surface, state, hovered_digit, mapper, footer_rect)

        pygame.display.flip()
        return door_rects
