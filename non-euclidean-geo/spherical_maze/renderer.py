import math
from typing import List, Tuple, Set, Optional
import pygame
import numpy as np
from .icosphere import face_center
from .geometry import spherical_distance, normalize
from .maze import Cell
from .projection import build_tangent_basis, project_geodesic, project_point
from .player import PlayerState

# Color Palette
COLOR_BG = (15, 20, 29)          # Deep slate void
COLOR_GRID_BG = (22, 30, 44)     # Viewport circle background
COLOR_CIRCLE_RING = (45, 60, 85) # Viewport boundary ring
COLOR_WALL = (0, 229, 255)       # Glowing cyan
COLOR_WALL_DIM = (0, 120, 150)   # Distant wall
COLOR_SELECTED = (255, 42, 133)  # Hot magenta / rose
COLOR_PLAYER = (255, 255, 255)    # White player arrow
COLOR_BREADCRUMB = (0, 255, 102) # Emerald green
COLOR_GOAL = (255, 215, 0)       # Gold
COLOR_HUD_TEXT = (220, 230, 245) # Light ice blue
COLOR_PANEL_BG = (10, 14, 22, 210) # Semi-transparent dark

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Main projection viewport center & pixel scale
        self.center = (self.width // 2, self.height // 2)
        self.view_radius_px = int(min(self.width, self.height) * 0.42)
        self.max_radius_rad = 1.5  # radians (slightly less than hemisphere)
        self.scale = self.view_radius_px / self.max_radius_rad
        
        pygame.font.init()
        self.font = pygame.font.SysFont("Consolas", 16)
        self.title_font = pygame.font.SysFont("Consolas", 20, bold=True)
        self.large_font = pygame.font.SysFont("Consolas", 32, bold=True)

    def get_effective_forward(self, player: PlayerState, cells: List[Cell]) -> np.ndarray:
        """Compute effective forward vector based on camera mode (transported vs stabilized)."""
        if player.camera_mode == "stabilized":
            target_id = player.get_selected_exit_cell_id(cells)
            if target_id is not None:
                q_target = cells[target_id].center
                d = spherical_distance(player.position, q_target)
                if d > 1e-7:
                    return normalize((q_target - np.cos(d) * player.position) / np.sin(d))
        return player.forward

    def render(self, player: PlayerState, cells: List[Cell], verts: np.ndarray, goal_cell_id: int, show_debug: bool = False) -> None:
        """Render complete frame."""
        self.screen.fill(COLOR_BG)
        
        # 1. Draw Viewport Background Circle
        pygame.draw.circle(self.screen, COLOR_GRID_BG, self.center, self.view_radius_px)
        pygame.draw.circle(self.screen, COLOR_CIRCLE_RING, self.center, self.view_radius_px, width=2)
        
        # Effective basis
        f_eff = self.get_effective_forward(player, cells)
        p, f, r = build_tangent_basis(player.position, f_eff)
        
        # 2. Draw Breadcrumbs
        for bc_id in player.breadcrumbs:
            q_bc = cells[bc_id].center
            proj = project_point(p, f, r, q_bc, self.scale, self.center, self.max_radius_rad)
            if proj:
                px, py, dist = proj
                alpha_factor = max(0.2, 1.0 - (dist / self.max_radius_rad))
                radius = max(3, int(8 * alpha_factor))
                pygame.draw.circle(self.screen, COLOR_BREADCRUMB, (int(px), int(py)), radius)
                
        # 3. Draw Maze Walls
        # Collect unique closed edges
        visible_wall_count = 0
        drawn_edges = set()
        
        for cell in cells:
            # Check distance from player to cull distant cells
            if spherical_distance(p, cell.center) > self.max_radius_rad + 0.3:
                continue
                
            v0, v1, v2 = cell.vertices
            face_edges = [
                (min(v0, v1), max(v0, v1)),
                (min(v1, v2), max(v1, v2)),
                (min(v2, v0), max(v2, v0))
            ]
            
            for edge in face_edges:
                if edge in drawn_edges:
                    continue
                
                # Determine if this edge is a closed wall
                # Find neighboring cells sharing this edge
                neigh_cells = [c for c in cells if edge[0] in c.vertices and edge[1] in c.vertices]
                
                is_wall = False
                if len(neigh_cells) == 1:
                    is_wall = True
                elif len(neigh_cells) == 2:
                    c1, c2 = neigh_cells[0], neigh_cells[1]
                    if c2.id not in c1.open_neighbors:
                        is_wall = True
                        
                if is_wall:
                    drawn_edges.add(edge)
                    pos_a = verts[edge[0]]
                    pos_b = verts[edge[1]]
                    
                    pts = project_geodesic(pos_a, pos_b, p, f, r, self.scale, self.center, samples=8, max_radius=self.max_radius_rad)
                    if len(pts) >= 2:
                        visible_wall_count += 1
                        avg_dist = sum(pt[2] for pt in pts) / len(pts)
                        fade = max(0.0, 1.0 - (avg_dist / self.max_radius_rad))
                        
                        # Interpolate wall color with distance fade
                        r_c = int(COLOR_WALL[0] * fade + COLOR_BG[0] * (1 - fade))
                        g_c = int(COLOR_WALL[1] * fade + COLOR_BG[1] * (1 - fade))
                        b_c = int(COLOR_WALL[2] * fade + COLOR_BG[2] * (1 - fade))
                        
                        screen_line = [(int(pt[0]), int(pt[1])) for pt in pts]
                        pygame.draw.lines(self.screen, (r_c, g_c, b_c), False, screen_line, width=2)

        # 4. Draw Selected Exit Highlight
        selected_target_id = player.get_selected_exit_cell_id(cells)
        if selected_target_id is not None:
            target_center = cells[selected_target_id].center
            proj = project_point(p, f, r, target_center, self.scale, self.center, self.max_radius_rad)
            if proj:
                px, py, _ = proj
                # Draw exit highlight corridor directional arrow / marker
                dir_x, dir_y = px - self.center[0], py - self.center[1]
                length = math.hypot(dir_x, dir_y)
                if length > 1e-3:
                    dir_x /= length
                    dir_y /= length
                    arrow_tip = (self.center[0] + dir_x * 35, self.center[1] + dir_y * 35)
                    pygame.draw.line(self.screen, COLOR_SELECTED, self.center, arrow_tip, width=4)
                    pygame.draw.circle(self.screen, COLOR_SELECTED, (int(px), int(py)), 6)

        # 5. Draw Goal Indicator
        q_goal = cells[goal_cell_id].center
        goal_dist = spherical_distance(p, q_goal)
        proj_goal = project_point(p, f, r, q_goal, self.scale, self.center, self.max_radius_rad)
        if proj_goal:
            gx, gy, _ = proj_goal
            # Diamond shape for goal
            size = 10
            diamond = [
                (gx, gy - size), (gx + size, gy),
                (gx, gy + size), (gx - size, gy)
            ]
            pygame.draw.polygon(self.screen, COLOR_GOAL, diamond)
            pygame.draw.polygon(self.screen, (255, 255, 255), diamond, width=2)
            
        # 6. Draw Fixed Player Arrow at Center
        self._draw_player_arrow()

        # 7. Draw HUD
        self._draw_hud(player, goal_dist, goal_cell_id == player.cell_id)

        # 8. Draw Debug Panel & Corner Globe if enabled
        if show_debug:
            self._draw_debug_overlay(player, cells, verts, goal_cell_id, visible_wall_count)

    def _draw_player_arrow(self) -> None:
        """Draw player indicator fixed at center of screen pointing UP."""
        cx, cy = self.center
        arrow = [
            (cx, cy - 14),       # Tip pointing UP
            (cx - 10, cy + 10),  # Bottom Left
            (cx, cy + 5),        # Inner notch
            (cx + 10, cy + 10)   # Bottom Right
        ]
        pygame.draw.polygon(self.screen, COLOR_PLAYER, arrow)
        pygame.draw.polygon(self.screen, COLOR_SELECTED, arrow, width=2)

    def _draw_hud(self, player: PlayerState, goal_dist: float, at_goal: bool) -> None:
        """Draw top and bottom HUD text bars."""
        # Top Bar
        top_text = f"Goal Distance: {goal_dist:.2f} rad | Breadcrumbs: {len(player.breadcrumbs)}"
        surf_top = self.font.render(top_text, True, COLOR_HUD_TEXT)
        self.screen.blit(surf_top, (20, 20))
        
        # Bottom Bar
        bot_text = f"Controls: 1/3 (Rotate) | Up/Enter (Move) | Space (Mark) | Cam: {player.camera_mode.capitalize()} [C] | Debug [Tab]"
        surf_bot = self.font.render(bot_text, True, COLOR_HUD_TEXT)
        self.screen.blit(surf_bot, (20, self.height - 35))
        
        if at_goal:
            win_surf = self.large_font.render("MAZE ESCAPED! GOAL REACHED!", True, COLOR_GOAL)
            rect = win_surf.get_rect(center=(self.width // 2, 70))
            self.screen.blit(win_surf, rect)

    def _draw_debug_overlay(
        self,
        player: PlayerState,
        cells: List[Cell],
        verts: np.ndarray,
        goal_cell_id: int,
        visible_wall_count: int
    ) -> None:
        """Draw debug panel and orthographic mini-globe."""
        # Panel container in top-right
        panel_w, panel_h = 320, 260
        panel_x = self.width - panel_w - 20
        panel_y = 20
        
        # Draw panel background surface with transparency
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COLOR_PANEL_BG)
        pygame.draw.rect(panel_surf, COLOR_CIRCLE_RING, (0, 0, panel_w, panel_h), width=2)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
        # Text Info
        lines = [
            "--- DEBUG OVERLAY ---",
            f"Cell ID: {player.cell_id} / {len(cells)}",
            f"Position: [{player.position[0]:.2f}, {player.position[1]:.2f}, {player.position[2]:.2f}]",
            f"Forward:  [{player.forward[0]:.2f}, {player.forward[1]:.2f}, {player.forward[2]:.2f}]",
            f"Visible Walls: {visible_wall_count}",
            f"Camera Mode: {player.camera_mode}"
        ]
        
        for idx, line in enumerate(lines):
            t_surf = self.font.render(line, True, COLOR_HUD_TEXT)
            self.screen.blit(t_surf, (panel_x + 15, panel_y + 12 + idx * 22))
            
        # Draw Mini Orthographic Globe in bottom of debug panel
        globe_cx = panel_x + panel_w // 2
        globe_cy = panel_y + 180
        globe_r = 55
        
        pygame.draw.circle(self.screen, (20, 30, 45), (globe_cx, globe_cy), globe_r)
        pygame.draw.circle(self.screen, COLOR_CIRCLE_RING, (globe_cx, globe_cy), globe_r, width=1)
        
        # Project cell centers orthographically (using XY plane, Z > 0 for front hemisphere)
        for cell in cells:
            cx, cy, cz = cell.center
            if cz > 0: # front hemisphere
                gx = globe_cx + int(cx * globe_r)
                gy = globe_cy - int(cy * globe_r)
                pygame.draw.circle(self.screen, (60, 80, 110), (gx, gy), 1)
                
        # Draw Goal on Mini Globe
        gz = cells[goal_cell_id].center[2]
        if gz > 0:
            gx = globe_cx + int(cells[goal_cell_id].center[0] * globe_r)
            gy = globe_cy - int(cells[goal_cell_id].center[1] * globe_r)
            pygame.draw.circle(self.screen, COLOR_GOAL, (gx, gy), 4)
            
        # Draw Player on Mini Globe
        pz = player.position[2]
        if pz > 0:
            px = globe_cx + int(player.position[0] * globe_r)
            py = globe_cy - int(player.position[1] * globe_r)
            pygame.draw.circle(self.screen, COLOR_SELECTED, (px, py), 5)
