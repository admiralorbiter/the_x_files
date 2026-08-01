from dataclasses import dataclass, field
from typing import List, Set, Optional, Tuple
import numpy as np
from .geometry import normalize, slerp, parallel_transport, spherical_distance, rotate_about_axis
from .projection import build_tangent_basis
from .maze import Cell

@dataclass
class PlayerState:
    cell_id: int
    position: np.ndarray
    forward: np.ndarray
    selected_exit_idx: int = 0
    
    # Movement Animation
    animating: bool = False
    anim_t: float = 0.0
    anim_speed: float = 4.0  # complete in 0.25s
    anim_from_pos: np.ndarray = field(default_factory=lambda: np.zeros(3))
    anim_to_pos: np.ndarray = field(default_factory=lambda: np.zeros(3))
    anim_from_fwd: np.ndarray = field(default_factory=lambda: np.zeros(3))
    anim_to_fwd: np.ndarray = field(default_factory=lambda: np.zeros(3))
    target_cell_id: int = -1
    
    # Gameplay State
    breadcrumbs: Set[int] = field(default_factory=set)
    visited: Set[int] = field(default_factory=set)
    camera_mode: str = "transported"  # "transported" or "stabilized"

    def get_sorted_exits(self, cells: List[Cell]) -> List[int]:
        """Return open neighbor cell IDs sorted by visual bearing around current forward vector."""
        curr_cell = cells[self.cell_id]
        open_neighs = list(curr_cell.open_neighbors)
        if not open_neighs:
            return []
            
        p, f, r = build_tangent_basis(self.position, self.forward)
        
        def calc_bearing(n_id: int) -> float:
            q = cells[n_id].center
            d = spherical_distance(p, q)
            if d < 1e-7:
                return 0.0
            t_vec = (q - np.cos(d) * p) / np.sin(d)
            return float(np.arctan2(np.dot(t_vec, r), np.dot(t_vec, f)))
            
        return sorted(open_neighs, key=calc_bearing)

    def get_selected_exit_cell_id(self, cells: List[Cell]) -> Optional[int]:
        exits = self.get_sorted_exits(cells)
        if not exits:
            return None
        idx = self.selected_exit_idx % len(exits)
        return exits[idx]

    def cycle_exit(self, direction: int, cells: List[Cell]) -> None:
        """Cycle selected exit (-1 for left, +1 for right)."""
        exits = self.get_sorted_exits(cells)
        if not exits:
            return
        self.selected_exit_idx = (self.selected_exit_idx + direction) % len(exits)

    def start_move(self, target_cell_id: int, cells: List[Cell]) -> None:
        """Initiate movement animation to target neighbor cell."""
        if self.animating:
            return
            
        self.animating = True
        self.anim_t = 0.0
        self.anim_from_pos = self.position.copy()
        self.anim_to_pos = cells[target_cell_id].center.copy()
        self.target_cell_id = target_cell_id
        
        self.anim_from_fwd = self.forward.copy()
        # End forward vector after parallel transport to destination
        self.anim_to_fwd = parallel_transport(self.forward, self.anim_from_pos, self.anim_to_pos)

    def auto_select_forward_exit(self, cells: List[Cell]) -> None:
        """Set selected_exit_idx to the exit closest to current forward heading."""
        exits = self.get_sorted_exits(cells)
        if not exits:
            self.selected_exit_idx = 0
            return
            
        p, f, r = build_tangent_basis(self.position, self.forward)
        
        def calc_abs_bearing(n_id: int) -> float:
            q = cells[n_id].center
            d = spherical_distance(p, q)
            if d < 1e-7:
                return 0.0
            t_vec = (q - np.cos(d) * p) / np.sin(d)
            bearing = float(np.arctan2(np.dot(t_vec, r), np.dot(t_vec, f)))
            return abs(bearing)
            
        best_exit_id = min(exits, key=calc_abs_bearing)
        self.selected_exit_idx = exits.index(best_exit_id)

    def update_animation(self, dt: float, cells: List[Cell]) -> None:
        """Advance animation state and update position/heading."""
        if not self.animating:
            return
            
        self.anim_t += dt * self.anim_speed
        if self.anim_t >= 1.0:
            self.anim_t = 1.0
            self.animating = False
            self.cell_id = self.target_cell_id
            self.position = self.anim_to_pos.copy()
            self.forward = self.anim_to_fwd.copy()
            self.visited.add(self.cell_id)
            self.auto_select_forward_exit(cells)
        else:
            # Interpolate position
            self.position = slerp(self.anim_from_pos, self.anim_to_pos, self.anim_t)
            # Parallel transport forward vector along the current motion segment
            self.forward = parallel_transport(self.anim_from_fwd, self.anim_from_pos, self.position)
            
    def turn_around(self, cells: List[Cell]) -> None:
        """Flip heading 180 degrees in tangent space."""
        self.forward = -self.forward
        self.auto_select_forward_exit(cells)

    def toggle_breadcrumb(self) -> None:
        """Place or remove breadcrumb at current cell."""
        if self.cell_id in self.breadcrumbs:
            self.breadcrumbs.remove(self.cell_id)
        else:
            self.breadcrumbs.add(self.cell_id)
