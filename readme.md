# The X Files — Experiments Repository

A collection of interactive coding experiments, physics simulations, and mathematical prototypes.

---

## 🧪 Experiments

### 1. [Spherical Maze Lab](file:///c:/Users/admir/Github/the_x_files/non-euclidean-geo/README.md) (`/non-euclidean-geo`)

An interactive non-Euclidean maze exploration game built with Python and Pygame.

- **Concept**: The player explores a maze rendered on the 2D surface of a 3D unit sphere ($S^2$) divided into triangular cells (icosphere level 2 mesh with 320 cells).
- **Player-Centered Projection**: Uses an **Azimuthal Equidistant Projection** where the player remains fixed at the screen center while the surrounding world distorts, bends, and rotates around them.
- **Geodesic SLERP Walls & Parallel Transport**: Wall edges curve along great-circle arcs, and moving through closed loops parallel-transports the player's 3D heading vector (demonstrating holonomy).
- **Inspirations**: *HyperRogue*, *Hyperbolica*, and *HOLONOMY*.
- **Run**:
  ```bash
  cd non-euclidean-geo
  python app.py
  ```