from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict, Optional
import random
import numpy as np
from collections import deque
from .icosphere import face_center, build_face_adjacency
from .geometry import spherical_distance

@dataclass
class Cell:
    id: int
    vertices: Tuple[int, int, int]
    center: np.ndarray
    neighbors: List[int]
    open_neighbors: Set[int] = field(default_factory=set)

def build_cells(verts: np.ndarray, faces: List[Tuple[int, int, int]]) -> List[Cell]:
    """Construct Cell objects with centers and neighbor lists."""
    adjacency = build_face_adjacency(faces)
    cells = []
    
    for i, face in enumerate(faces):
        center = face_center(verts, face)
        neighs = adjacency[i]
        cell = Cell(
            id=i,
            vertices=face,
            center=center,
            neighbors=neighs,
            open_neighbors=set()
        )
        cells.append(cell)
        
    return cells

def generate_maze(cells: List[Cell], seed: Optional[int] = None, loop_prob: float = 0.08) -> None:
    """
    Generate a maze on the cell graph using randomized DFS.
    Also reopens loop_prob fraction of closed walls to create closed loops.
    """
    if seed is not None:
        random.seed(seed)
        
    # Reset open neighbors
    for cell in cells:
        cell.open_neighbors.clear()
        
    visited: Set[int] = set()
    start_id = random.randint(0, len(cells) - 1)
    
    stack = [start_id]
    visited.add(start_id)
    
    closed_edges: List[Tuple[int, int]] = []
    
    while stack:
        current = stack[-1]
        unvisited_neighs = [n for n in cells[current].neighbors if n not in visited]
        
        if unvisited_neighs:
            next_cell = random.choice(unvisited_neighs)
            cells[current].open_neighbors.add(next_cell)
            cells[next_cell].open_neighbors.add(current)
            visited.add(next_cell)
            stack.append(next_cell)
        else:
            stack.pop()
            
    # Collect remaining closed edges
    all_closed: Set[Tuple[int, int]] = set()
    for cell in cells:
        for n in cell.neighbors:
            if n not in cell.open_neighbors:
                edge = (min(cell.id, n), max(cell.id, n))
                all_closed.add(edge)
                
    # Reopen a small percentage of walls to introduce loops
    closed_list = list(all_closed)
    random.shuffle(closed_list)
    num_to_open = int(len(closed_list) * loop_prob)
    
    for u, v in closed_list[:num_to_open]:
        cells[u].open_neighbors.add(v)
        cells[v].open_neighbors.add(u)

def find_start_goal(cells: List[Cell]) -> Tuple[int, int]:
    """Find start cell (closest to north pole) and goal cell (farthest graph distance)."""
    # Start: cell closest to [0, 0, 1]
    start_id = min(range(len(cells)), key=lambda i: spherical_distance(cells[i].center, np.array([0.0, 0.0, 1.0])))
    
    # BFS to find cell with greatest graph distance from start
    dist: Dict[int, int] = {start_id: 0}
    queue = deque([start_id])
    
    farthest_cell = start_id
    max_dist = 0
    
    while queue:
        curr = queue.popleft()
        d = dist[curr]
        if d > max_dist:
            max_dist = d
            farthest_cell = curr
            
        for n in cells[curr].open_neighbors:
            if n not in dist:
                dist[n] = d + 1
                queue.append(n)
                
    return start_id, farthest_cell
