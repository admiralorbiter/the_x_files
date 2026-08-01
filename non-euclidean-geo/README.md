# Spherical Maze Lab — Non-Euclidean Geometry Experiment

An interactive 2D player-centered visualization and maze explorer operating on the surface of a unit sphere ($S^2$). 

Rather than moving a camera across a flat map, the player remains fixed at the screen center while the world continuously distorts, bends, rotates, expands, and contracts around them using an **Azimuthal Equidistant Projection**.

---

## 🌟 Key Features & Concepts

### 1. Player-Centered Azimuthal Equidistant Projection
- Radial screen distance corresponds directly to true spherical geodesic distance ($d = \arccos(\mathbf{p} \cdot \mathbf{q})$).
- Screen angle corresponds to the initial bearing from the observer to the target point.
- The observer maps to the center of the screen, eliminating the need for traditional flat-camera coordinates.

### 2. Icosphere Dual-Graph World
- The world is constructed by subdividing an icosahedron into 320 triangular cells (Subdivision Level 2).
- Each triangle represents a maze cell; shared edges are either open corridors or solid walls.
- Maze paths are generated via a randomized Depth-First Search (DFS) with ~8% loop reopening to create closed loops where curved-space effects can be observed.

### 3. Geodesic Arc Tessellation (SLERP Wall Drawing)
- Straight screen lines cannot represent curved 3D spherical edges accurately.
- Walls are sampled into multiple intermediate points along great-circle arcs using **Spherical Linear Interpolation (SLERP)** and projected individually into polyline screen coordinates.

### 4. Parallel Transport & Heading Holonomy
- Moving between cells parallel-transports the player's 3D forward tangent vector along geodesic paths.
- Traveling around closed loops on the sphere causes **holonomy**—returning to an earlier location leaves the player facing a shifted apparent direction!

### 5. Sticky Forward Exit Selection
- Upon entering a cell or turning around, exit selection automatically defaults to the corridor pointing straightest forward in your current heading direction. You can continuously press **Up** to traverse straight hallways.

### 6. Dual Camera Modes
- **Transported Mode**: Authentic mathematical orientation; orientation changes when traveling loops.
- **Stabilized Mode**: Camera smoothly aligns to keep the currently selected exit facing upward.

### 7. Debug Panel & Orthographic Mini-Globe
- Pressing `Tab` opens a debug panel showing 3D vectors, visible wall counts, and an orthographic 3D mini-globe preview.

---

## 💡 Inspirations & Prior Art

This experiment was inspired by playing **HyperRogue** and exploring non-Euclidean geometry in games and interactive software:

* **HyperRogue**: Uses a hyperbolic plane and turns its exponential expansion, unusual tilings, difficult return journeys, and accumulated rotation into core gameplay mechanics. Its engine now supports dozens of geometries and projections.
* **Hyperbolica**: Places the player in first-person hyperbolic and spherical environments, building mazes, platforming, races, and shooting minigames around their differing spatial behaviors.
* **HOLONOMY**: A research prototype in which users physically walk through an effectively infinite hyperbolic environment. Its developers specifically solved curved-space rendering, object placement, navigation, and shortest-path problems.

---

## 📝 Prototype Wrap-Up & Notes

This project served as a focused prototype to explore non-Euclidean geometry and build a complete, self-contained interactive experiment. 

Separating the abstract graph layer (cells and maze logic) from the continuous geometry layer (spherical vectors, SLERP, and projection) provides a solid foundation. If returning to non-Euclidean geometry projects in the future—such as expanding into hyperbolic space ($H^2$), Poincar&eacute; disk models, or higher-dimensional manifolds—this codebase provides an extensible template to build upon.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.9+
- `pygame` and `numpy`

```bash
pip install -r requirements.txt
```

### Running the App
```bash
python app.py
```

---

## 🎮 Controls

| Key | Action |
| --- | --- |
| **Left / Right (1 / 3, A / D)** | Cycle selected exit left/right |
| **Up / Enter / W** | Move through selected exit |
| **Down / S** | Turn around (180° flip) |
| **Space** | Place/Remove breadcrumb marker |
| **C** | Toggle Camera Mode (*Transported* / *Stabilized*) |
| **Tab** | Toggle Debug Panel & Mini-Globe Preview |
| **R** | Re-seed and generate a new maze |
| **Esc** | Quit |

---

## 📁 Code Architecture

```
non-euclidean-geo/
├── app.py                     # Main application entry point & event loop
├── requirements.txt           # Dependency specifications
├── README.md                  # Project documentation
├── spherical_maze/
│   ├── __init__.py
│   ├── geometry.py            # Slerp, spherical distance, Rodrigues rotation, parallel transport
│   ├── icosphere.py           # Icosphere mesh generation & triangular face adjacency
│   ├── maze.py                # Dual graph DFS maze generation & start/goal search
│   ├── projection.py          # Azimuthal equidistant projection & geodesic sampling
│   ├── player.py              # Player state, orientation, sticky exit selection, slerp animation
│   └── renderer.py            # Pygame rendering, wall fading, HUD, debug mini-globe
└── tests/
    ├── test_geometry.py       # Unit tests for geometry primitives
    ├── test_mesh.py           # Unit tests for mesh structure & maze reciprocity
    └── test_projection.py     # Unit tests for projection accuracy
```
