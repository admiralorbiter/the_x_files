# The X Files — Experiments Repository

A collection of interactive coding experiments, physics simulations, and mathematical prototypes.

---

## 🧪 Experiments

### 3. [Momentum Maze: Pendulum Vault](file:///c:/Users/admir/Github/the_x_files/momentum-maze/README.md) (`/momentum-maze`)

A pulse-based control puzzle in which the player steers a physical pendulum through hand-designed challenge rooms by navigating its phase portrait.

- **Concept**: The player's position is the state $(\theta, \omega)$ — angle and angular velocity simultaneously. The phase space is the actual world, not a HUD overlay. The physical pendulum view and the mathematical phase-portrait view are equally prominent at all times.
- **Mechanic**: At each decision point, the player chooses one of three bounded torque pulses ($-u_{\max}$, $0$, $+u_{\max}$). Three predicted trajectories are always visible before committing. Planning happens in stillness; execution is deterministic.
- **Research question**: Can navigating a phase portrait become an understandable and engaging game mechanic without formal mathematical vocabulary?
- **Math**: Nonlinear pendulum ODE on the phase cylinder $S^1 \times \mathbb{R}$, fixed-step RK4 integration, energy contours, separatrix at $E=2$, pulse-energy shaping $\dot{E}=u\omega$.
- **Run**:
  ```bash
  cd momentum-maze
  pip install -r requirements.txt
  python main.py
  ```

---

### 2. [The Binary House](file:///c:/Users/admir/Github/the_x_files/binary-house/README.md) (`/binary-house`)

An experimental mathematical puzzle-stealth game built with Python and Pygame.

- **Concept**: The player explores a house whose 256 rooms are arranged according to **2-adic (ultrametric) distance** rather than Euclidean distance. Two rooms are close when their 8-digit binary addresses share their earliest (low-order) digits.
- **Mechanic**: Every door toggles exactly one address digit. Changing an early digit is a large move; changing a late digit is nearly imperceptible. The player steals three seals and escapes while avoiding the Caretaker — an enemy that detects by shared address prefix rather than line of sight.
- **Research question**: Can players learn and exploit an ultrametric notion of distance through play, without prior knowledge of p-adic mathematics?
- **Math**: Finite approximation of ℤ/2⁸ℤ with deterministic prefix-tree procedural generation, hierarchical sound propagation, and optional affine isometry mechanics.
- **Run**:
  ```bash
  cd binary-house
  pip install -r requirements.txt
  python app.py
  ```

---

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