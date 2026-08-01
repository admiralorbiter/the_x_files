# The House That Remembers (The Binary House)

> *A house that recognizes family resemblance rather than physical location.*

**The House That Remembers** (project code name *The Binary House*) is an experimental mathematical stealth-puzzle game in which rooms are arranged according to **2-adic (ultrametric) distance** rather than Euclidean distance.

Instead of navigating by North/South/East/West or 2D coordinates, rooms inherit their identity through an **ancestral prefix tree** (Foundation $\to$ Wing $\to$ Household $\to$ Memory). Two rooms are *close* when they share their earliest inherited traits. A wardrobe door changes only a deep memory digit and leaves the player virtually unmoved. A front door changes the foundational architecture and transports the player into a completely different branch of the house.

The prototype is both a game and a mathematical interface-design experiment. Its primary question:

> **Can players learn and exploit an ultrametric notion of distance through play, without any prior knowledge of p-adic mathematics?**

---

## Designer's Notes & Reflections

> *"This is one of the more interesting experiments because it allows you to construct really complex puzzles built around mathematical mechanics we already understand. You don't have to worry about whether the underlying puzzle mechanics will 'work out' in the end — you build around math you already know is rigorous, and then explore the downstream design effects from there."*

- **Intuition & Learning Curve**: The core mechanics present a fascinating puzzle space. Reminiscent in spirit of games like *Blue House*, there is huge potential to build player intuition around resemblance and non-Euclidean distance through perception, consequence, and story.
- **Narrative & Environmental Depth**: Further iteration will involve playing through scenarios extensively, deepening the story and lore around the house, and refining how spatial memory and lineage clues communicate the 2-adic structure naturally.
- **Formally Grounded Level Design**: Because 2-adic ultrametric space guarantees rigid invariant properties (strong triangle inequality, isometric affine transformations, strictly nested neighborhood balls), puzzle logic is mathematically guaranteed to be consistent. The design challenge shifts entirely to perceptual presentation: guiding players to develop an intuitive mental model of ultrametric space through play.

---

## Quick Start

```bash
cd binary-house
pip install -r requirements.txt

# Run default player-facing diegetic view (The House That Remembers)
python app.py --depth 4

# Run 64-room world with active Caretaker enemy
python app.py --depth 6

# Start directly in F2 Mathematical Debug View
python app.py --depth 6 --debug
```

Python 3.12+ and Pygame are required.

---

## View Modes & Controls

| View Mode | Hotkey | Description |
|---|---|---|
| **Diegetic View** | Default | Player-facing horror UI (*The House That Remembers*). Speaks in terms of lineage, wings, echoes, and door previews. |
| **Archivist View** | `F1` | Reveals nested house memory structure and wing names. |
| **Mathematical Debug View** | `F2` | Exposes raw 2-adic addresses ($b_0 \cdot b_1 \dots$), ball sizes, bit operations, and distance exponents ($2^{-k}$). |

---

## Mathematical & Fiction Translation

The space is the finite ring **ℤ/2⁸ℤ** — a faithful truncation of the 2-adic integers that preserves the hierarchical distance structure while bounding the world to exactly 256 leaf rooms.

### 2-adic distance

```
d₂(x, y) = 2^(−v₂(x − y))
```

where `v₂(n)` is the largest power of 2 dividing `n`.

Equivalently: two rooms are at distance `2^(−k)` when their addresses first differ at digit *k* (counting from the low-order end).

### Translation Table

| 2-Adic Math Concept | Fiction Concept | Example |
|---|---|---|
| Address ($b_0 \cdot b_1 \cdot b_2 \cdot b_3$) | House Lineage | `Wooden · Moon Wing · Candle · Eye` |
| Bit $b_0$ | Foundation | `Wooden` (0) vs `Stone` (1) |
| Bit $b_1$ | Wing | `Moon Wing` (0) vs `Sun Wing` (1) |
| Bit $b_2$ | Household | `Candle` (0) vs `Bell` (1) |
| Bit $b_3$ | Memory | `Eye` (0) vs `Moth` (1) |
| Ultrametric Ball $B_k(x)$ | House Memory / Wing | `"The Wooden Moon Wing"` |
| Distance $2^{-k}$ | Echo level | `"Very close — same household"` |
| Door Toggle ($x \oplus 2^k$) | Physical Passage | Front Door (0), Stairwell (1), Interior Door (2), Wardrobe (3) |

---

## Architecture

```
binary-house/
├── binary_house/
│   ├── core/                 # 2-Adic Mathematical Kernel
│   │   ├── address.py        # Address dataclass (Z/2^n Z) & near-first formatting
│   │   ├── ball.py           # Ball membership, containment, parent/children, topology
│   │   ├── door.py           # ToggleDigit (x XOR 2^k) & AffineDoor (odd multiplier isometry)
│   │   └── metric.py         # 2-adic valuation v₂(n) & distance_level k
│   ├── world/                # World Model & Procedural Generation
│   │   ├── room.py           # RoomStyle & Room dataclasses
│   │   ├── generator.py      # Seeded prefix-tree room style & door generation
│   │   └── world.py          # World graph generator with seal & exit placement
│   ├── game/                 # Turn-Based Game Engine & AI
│   │   ├── state.py          # GameState turn resolution engine & event log
│   │   ├── caretaker.py      # Caretaker AI search ball & prefix detection logic
│   │   ├── sound.py          # SoundRegion hierarchical expansion through parent balls
│   │   └── player.py         # Player actions (Move, Chalk, QuietSteps, Wait)
│   └── ui/                   # User Interface & Audio Synthesis
│       ├── fiction.py        # Math <-> Fiction translation mapper
│       ├── diegetic_renderer.py # Player-facing diegetic view compositor
│       ├── debug_renderer.py # F2 Mathematical Debug View
│       ├── renderer.py       # Unified view dispatcher (Diegetic / Archivist / Debug)
│       ├── hud.py            # Address ribbon, neighborhood stack, scale ledger
│       ├── assets.py         # Layered procedural room art & custom geometric icons
│       ├── transitions.py    # Layer-preserving transition animation engine
│       ├── audio.py          # Additive runtime audio synthesizer for digits b₀, b₁, b₂
│       └── tutorial.py       # 5-scene onboarding sequence state machine
├── tests/                    # 24 Automated Unit & Exhaustive Topology Tests
├── app.py                    # Main executable entry point
├── requirements.txt
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## Current Status & Milestones

| Milestone | Status | Description |
|---|---|---|
| **Milestone 0: Mathematical Kernel** | ✅ **COMPLETED** | Exhaustive 262k strong triangle inequality check & ball topology tests passing. |
| **Milestone 1: Navigation Instrument** | ✅ **COMPLETED** | 16-room world, procedural visual layers, additive audio synthesis. |
| **Fiction Shell ("The House That Remembers")** | ✅ **COMPLETED** | Diegetic view, custom geometric lineage icons, House Memory nested frames, Echoes panel, door previews, F1/F2 mode toggle, tutorial sequence. |
| **Milestone 2: Deep Stealth Loop** | ✅ **COMPLETED** | Caretaker AI search, frustration widening, relational seal clues, victory/capture screens. |
| **Milestone 3: Distraction Tools** | ✅ **COMPLETED** | Quiet Steps, Chalking, Lineage Lures (`LureRegion`), Branch Keys. |
| **Milestone 4: Eight Rooms Deep** | ✅ **COMPLETED** | Full 256-room 8-bit world, 5 multi-scale seals, Caretaker Heat System. |
| **Milestone 5: Arithmetic Mutation** | ✅ **COMPLETED** | Affine isometry house rearrangement ($x \mapsto 3x + 1$) & $2\times$ contraction elevator. |
