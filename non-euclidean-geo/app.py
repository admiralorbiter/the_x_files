import sys
import os
import pygame
import numpy as np

# Ensure spherical_maze package can be imported directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spherical_maze.icosphere import create_icosahedron, subdivide_mesh, face_center
from spherical_maze.maze import build_cells, generate_maze, find_start_goal
from spherical_maze.geometry import normalize
from spherical_maze.player import PlayerState
from spherical_maze.renderer import Renderer

def create_initial_forward(pos: np.ndarray) -> np.ndarray:
    """Create a valid initial tangent vector perpendicular to position."""
    ref = np.array([0.0, 1.0, 0.0]) if abs(pos[2]) > 0.8 else np.array([0.0, 0.0, 1.0])
    return normalize(np.cross(pos, ref))

def main():
    pygame.init()
    screen_width, screen_height = 1024, 768
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Spherical Maze Lab — Non-Euclidean Geometry Experiment")
    
    clock = pygame.time.Clock()
    renderer = Renderer(screen)
    
    # 1. Build Mesh & Graph
    print("Generating Icosphere mesh (Subdivision Level 2)...")
    verts, faces = create_icosahedron()
    verts, faces = subdivide_mesh(verts, faces, levels=2)
    cells = build_cells(verts, faces)
    
    # 2. Generate Maze
    print(f"Generating Maze across {len(cells)} cells...")
    generate_maze(cells, loop_prob=0.08)
    start_id, goal_id = find_start_goal(cells)
    
    # 3. Setup Player
    start_pos = cells[start_id].center.copy()
    start_fwd = create_initial_forward(start_pos)
    
    player = PlayerState(
        cell_id=start_id,
        position=start_pos,
        forward=start_fwd
    )
    player.visited.add(start_id)
    player.auto_select_forward_exit(cells)
    
    show_debug = False
    running = True
    
    print("\n--- Spherical Maze Lab Ready ---")
    print("Controls:")
    print("  Left / Right Arrow (or 1/3, A/D): Cycle exit selection")
    print("  Up Arrow (or Enter, W): Move into selected corridor")
    print("  Down Arrow (or S): Turn around 180°")
    print("  Space: Place/Remove breadcrumb")
    print("  C: Toggle Camera Mode (Transported / Stabilized)")
    print("  Tab: Toggle Debug Panel & Mini-Globe")
    print("  R: Reset & Generate New Maze")
    print("  Esc: Quit\n")

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_LEFT, pygame.K_1, pygame.K_a):
                    player.cycle_exit(-1, cells)
                elif event.key in (pygame.K_RIGHT, pygame.K_3, pygame.K_d):
                    player.cycle_exit(1, cells)
                elif event.key in (pygame.K_UP, pygame.K_RETURN, pygame.K_w):
                    target_id = player.get_selected_exit_cell_id(cells)
                    if target_id is not None:
                        player.start_move(target_id, cells)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    player.turn_around(cells)
                elif event.key == pygame.K_SPACE:
                    player.toggle_breadcrumb()
                elif event.key == pygame.K_TAB:
                    show_debug = not show_debug
                elif event.key == pygame.K_c:
                    player.camera_mode = "stabilized" if player.camera_mode == "transported" else "transported"
                elif event.key == pygame.K_r:
                    # Regenerate maze
                    generate_maze(cells, loop_prob=0.08)
                    start_id, goal_id = find_start_goal(cells)
                    start_pos = cells[start_id].center.copy()
                    player.cell_id = start_id
                    player.position = start_pos
                    player.forward = create_initial_forward(start_pos)
                    player.breadcrumbs.clear()
                    player.visited.clear()
                    player.visited.add(start_id)
                    player.auto_select_forward_exit(cells)

        # Update animation
        player.update_animation(dt, cells)
        
        # Render frame
        renderer.render(player, cells, verts, goal_id, show_debug)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
