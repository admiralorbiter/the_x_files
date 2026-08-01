# Momentum Maze: Pendulum Vault

> *The player is not a character moving through a map. The player is a point moving through a phase portrait.*

**Momentum Maze** is a control puzzle game built in Python and Pygame in which the player steers a physical pendulum through six hand-designed challenge rooms by issuing bounded torque pulses.

The player's position is a point $(\theta, \omega)$ in phase space — angle and angular velocity simultaneously. The phase portrait is not a HUD overlay. It **is** the world.

The prototype's central question:

> **Can navigating a phase portrait become an understandable and engaging game mechanic?**

---

## Designer's Notes & Reflections

> *"The beautiful thing about the pendulum as a starting system is that its phase portrait already contains everything you need for a dungeon. Fixed points are rest stops. The separatrix is a wall between worlds. Energy contours are the terrain. The player's only job is to learn to read this map and steer through it with a very small motor."*

- **Mathematical Grounding**: Every obstacle, gate, and hazard is derived directly from the pendulum's nonlinear dynamics. No arbitrary geometry is added to the phase space. A speed barrier exists because high angular velocity would stress the mechanism. A directional gate exists because the physical latch only catches clockwise motion. The math and the fiction agree at every point.

- **Pulse-Based Control**: The core UX decision — replacing continuous joystick control with discrete torque pulses — is the most important design choice in the prototype. It creates a **read → predict → pulse → travel → reconsider** rhythm and prevents the game from becoming a twitch-reflex experience. Each pulse lasts exactly 0.35 seconds. Planning happens in stillness.

- **Tactile Feedback & Visual Readability**: The pulse-based control loop combined with side-by-side phase space mapping creates an immediate, highly satisfying **read → predict → pulse → travel** rhythm. Players can pick it up instantly without prior control theory knowledge.

- **Future Synthesis ("We Got To Get Out Of This Place")**: The core mechanic of steering through state space rather than direct position choice has strong potential to serve as one module within a larger, multi-system escape game featuring gravity wells, wormholes, and non-Euclidean state transfers.

- **Dual-View Philosophy**: The physical pendulum view and the phase-space view must be equally prominent at all times. Neither is the "real" view. Players who can only read one are playing at a disadvantage. A critical acceptance condition for this prototype is that at least one chamber should be **extremely difficult using only the physical view** but **immediately understandable when reading phase space**.

- **Mathematical Discovery Without Vocabulary**: The prototype deliberately withholds formal terminology until the player has experienced the behavior it names. Players should discover that pushing with the pendulum's motion adds energy — and that this matters — before they ever see the word "energy." The separatrix should feel like a membrane long before it is labeled.

---

## Quick Start

```bash
cd momentum-maze
pip install -r requirements.txt

# Run from Chamber 0 (tutorial, no controls)
python main.py

# Start at a specific chamber
python main.py --chamber 3

# Enable debug overlay (vector field, energy values, state readout)
python main.py --debug
```

Python 3.11+ and Pygame are required. NumPy is used for vectorized phase-field calculations.

---

## Controls

| Action             | Key / Input         |
|--------------------|---------------------|
| Apply left torque  | `←` or `A`          |
| Coast (no torque)  | `↓` or `S`          |
| Apply right torque | `→` or `D`          |
| Commit selected pulse | `Space` or `Enter` |
| Restart chamber    | `R`                 |
| Toggle overlays    | `Tab`               |
| Toggle debug view  | `F1`                |
| Quit               | `Escape` or `Q`     |

Predicted trajectories for all three torque options are always visible. Commit is required before any pulse executes — the game is never real-time during planning.

---

## Mathematical Model

The pendulum obeys:

$$\dot{\theta} = \omega$$

$$\dot{\omega} = -\sin\theta - \beta\omega + u$$

with normalized units ($m = l = g = 1$), damping $\beta = 0.06$, and torque limit $|u| \leq u_{\max} = 0.35$.

The player may apply:

$$u \in \{-u_{\max},\ 0,\ +u_{\max}\}$$

for a pulse duration $\tau = 0.35$ seconds per committed action.

### Energy

$$E(\theta, \omega) = \tfrac{1}{2}\omega^2 + 1 - \cos\theta$$

| State | Energy |
|---|---|
| Downward equilibrium $(\theta=0, \omega=0)$ | $E = 0$ |
| Separatrix (boundary between swing and rotation) | $E = 2$ |
| Upright equilibrium $(\theta=\pi, \omega=0)$ | $E = 2$ |

The separatrix at $E = 2$ is the most important geometric feature in the game. States below it oscillate; states above it rotate. The final chamber requires the player to cross it in both directions.

### Effect of Control on Energy

$$\dot{E} = u\omega$$

Pushing **with** the direction of motion adds energy. Pushing **against** it removes energy. Pushing when $\omega \approx 0$ has almost no effect.

This is the game's core discovery.

---

## Phase Space & UI Layout

```
┌────────────────────────────┬─────────────────────────────┐
│                            │                             │
│     PHYSICAL MECHANISM     │       PHASE DUNGEON         │
│                            │                             │
│            ● pivot         │   ω                         │
│            │               │   ↑       hazard            │
│            │               │   │   ██████████            │
│            ◉ bob           │   │      ···╮               │
│                            │   │       ● ╰····            │
│                            │   └────────────────→ θ       │
│                            │      -π    0     π           │
├────────────────────────────┴─────────────────────────────┤
│ Energy 1.42     Pulse: RIGHT     Cost: 2     Target: DOCK│
└──────────────────────────────────────────────────────────┘
```

The phase view axis ranges are $\theta \in [-\pi, \pi)$ and $\omega \in [-4, 4]$.

Phase space is a **cylinder**: the left and right boundaries ($\theta = -\pi$ and $\theta = \pi$) represent the same angle. Crossing one boundary wraps the state marker to the other side.

---

## Chamber Sequence

| # | Name | Goal | New Concept |
|---|---|---|---|
| 0 | **The Moving Point** | Watch — no controls | Linked views, phase flow, wrapping |
| 1 | **Arrive Quietly** | Reach $\|\theta\|<0.12$, $\|\omega\|<0.15$ | Removing energy by opposing motion |
| 2 | **The Momentum Gate** | Cross $\theta=1.0$ with $0.7<\omega<1.2$ | Simultaneous position and velocity control |
| 3 | **Pump** | Complete one full rotation | Energy shaping across multiple swings |
| 4 | **Cross and Return** | Collect rotation key, return to oscillation, dock | Separatrix crossing in both directions |
| 5 | **Pendulum Vault** | Pass two state gates, avoid hazard, reach upright dock | Full phase-space maze |

---

## Architecture

```
momentum-maze/
├── main.py
├── simulation/
│   ├── state.py          # PendulumState & PendulumParameters dataclasses
│   ├── pendulum.py       # Derivative function (RHS of EOM)
│   ├── integrator.py     # Fixed-step RK4 integrator
│   └── predictor.py      # Trajectory preview (same code as committed gameplay)
│
├── game/
│   ├── level.py          # Chamber loader & active game state
│   ├── constraints.py    # PhaseConstraint protocol & all gate/hazard types
│   ├── objectives.py     # Completion & failure condition checking
│   ├── scoring.py        # Pulse count & control-effort tracking
│   └── replay.py         # Attempt recorder & playback engine
│
├── rendering/
│   ├── physical_view.py  # Pendulum animation, gates, motion trail
│   ├── phase_view.py     # Phase portrait, state marker, trajectory trails
│   ├── vector_field.py   # Arrow field & energy contour renderer
│   └── ui.py             # HUD, status bar, pulse selector
│
├── levels/
│   ├── chamber_00.json
│   ├── chamber_01.json
│   ├── chamber_02.json
│   ├── chamber_03.json
│   ├── chamber_04.json
│   └── chamber_05.json
│
└── tests/
    ├── test_energy.py       # E(θ,ω) formula & contour accuracy
    ├── test_integrator.py   # Conservation, damping, RK4 vs reference
    ├── test_constraints.py  # Gate, hazard, energy-lock, rotation key
    ├── test_wrapping.py     # Cylinder topology & boundary continuity
    └── test_prediction.py   # Committed path ≡ previewed path
```

---

## Prototype Success Criteria

1. The simulation is fully deterministic.
2. Predicted and committed trajectories match within floating-point tolerance.
3. Phase space wraps correctly at $\theta = \pm\pi$.
4. Energy contours and the separatrix visually match simulated behavior.
5. All six chambers are completable under their torque limits.
6. A new player can complete Chamber 2 without knowing formal phase-space terminology.
7. Players use the phase view deliberately by Chamber 4.
8. Players can verbally explain why arriving at the correct angle with the wrong velocity fails.
9. At least two valid pulse sequences solve Chamber 5.
10. The experience remains engaging after the initial mathematical novelty is understood.

---

## Current Status

| Milestone | Status | Description |
|---|---|---|
| **Folder & README** | ✅ **DONE** | Repository structure established |
| **Implementation Plan** | 🔄 **IN PROGRESS** | Detailed technical specification |
| **Simulation Core** | ⬜ Pending | State, integrator, predictor |
| **Phase-Space Renderer** | ⬜ Pending | Vector field, contours, separatrix |
| **Physical View** | ⬜ Pending | Pendulum animation, linked highlighting |
| **Game Loop & Constraints** | ⬜ Pending | Pulse logic, gate detection, scoring |
| **Chamber 0–2** | ⬜ Pending | Tutorial + first two puzzle rooms |
| **Chamber 3–5** | ⬜ Pending | Energy shaping + full vault sequence |
| **Replay System** | ⬜ Pending | Attempt recording & playback |
| **Test Suite** | ⬜ Pending | Mathematical validation |
