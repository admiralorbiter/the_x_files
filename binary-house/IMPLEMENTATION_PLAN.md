# The Binary House — Implementation Plan

A turn-based puzzle-stealth prototype built in Python + Pygame, in which all spatial relationships, enemy detection, sound propagation, and puzzle logic are grounded in **2-adic (ultrametric) distance**.

The project is both a game (**The House That Remembers**) and a mathematical interface-design experiment.

---

## Decisions & Resolved Status

> [!NOTE]
> **Milestones 0 through 5: ALL COMPLETED & TESTED (40/40 Passing Unit Tests)**.
> All components from core math kernel, navigation instrument, diegetic fiction layer, stealth loop, distraction tools, 256-room 8-bit world, and arithmetic mutations (rearrangement & contraction) are fully implemented and verified.

> [!NOTE]
> **Visual representation style** — **Diegetic Renderer with Procedural Compositing & Drawn Lineage Icons**.
> Rooms are rendered as room-dominant interiors with layered procedural visual composition. Ribbon icons are custom geometric vector drawings (Tree/Tower, Moon/Sun, Candle/Bell, Eye/Moth).

> [!NOTE]
> **Audio inheritance** — Additive audio motifs for digits $b_0, b_1, b_2$ synthesized at runtime via Pygame.

> [!NOTE]
> **Progressive disclosure world sizes** — Parameterized via `--depth` (4 for M1 tutorial, 6 for M2/M3 stealth loop, 8 for M4/M5 256-room full scenarios).

---

## Architecture & Completed Components

### Component 1 — Mathematical Kernel (`binary_house/core/`) ✅

- `address.py`: `Address` dataclass ($\mathbb{Z}/2^n\mathbb{Z}$), bit extraction, near-first formatting.
- `metric.py`: 2-adic valuation $v_2(n)$, `distance_level(a, b)` ($k$), `distance_float(a, b)` ($2^{-k}$).
- `ball.py`: `Ball` dataclass ($B_k(x)$), membership `contains()`, size, parent, children, static topological `relationship()` (equal, nested, disjoint).
- `door.py`: `ToggleDigit` ($x \oplus 2^k$), `AffineDoor` ($x \mapsto ax + b \bmod 2^n$ odd multiplier isometry).
- `contraction.py`: `contract_2x` ($x \mapsto 2x \bmod 2^n$).

### Component 2 — World Model (`binary_house/world/`) ✅

- `room.py`: `RoomStyle` (8-layer prefix-derived traits) and `Room` dataclass.
- `generator.py`: Seeded prefix-tree style mutation & door availability generator.
- `world.py`: `generate_world()` populates room graph, multi-scale seals (3 seals for $\le 6$-bit, 5 seals for 8-bit), relational clues (`make_relational_clue()`), exit ball, and scattered resources.
- `machine.py`: `RearrangementMachine` providing thematic named affine isometries ("The Folding", "The Inversion", "The Drift").

### Component 3 — Game Logic (`binary_house/game/`) ✅

- `state.py`: `GameState` turn resolution engine, event log, win/capture checks, `rearrange_world()`, `apply_contraction()`.
- `caretaker.py`: `CaretakerState` AI, search ball, frustration counter, heat level system (`effective_detection_depth`), `recognized_layers()`.
- `sound.py`: `SoundRegion` hierarchical expansion through parent balls.
- `lure.py`: `LureRegion` decoy lineage baiting.
- `player.py`: `MoveAction`, `UseChalk`, `UseQuietSteps`, `UseLure`, `BranchKeyAction`, `RearrangeAction`, `ContractAction`, `WaitAction`.

### Component 4 — UI & Diegetic Presentation (`binary_house/ui/`) ✅

- `fiction.py`: `FictionMapper` single source of truth for math $\leftrightarrow$ fiction translation.
- `diegetic_renderer.py`: Player-facing diegetic view compositor (Lineage Ribbon, House Memory nested frames, Echoes panel, Door Preview footer, Seals counter).
- `debug_renderer.py`: F2 Mathematical Debug View (raw addresses, distance exponents).
- `renderer.py`: Unified view dispatcher (Diegetic / Archivist / Debug mode switching).
- `hud.py`: Ribbon, neighborhood stack, scale ledger rendering.
- `assets.py`: Custom geometric lineage icons & composite procedural room interior art.
- `transitions.py`: Layer-preserving transition animation engine.
- `audio.py`: Additive runtime audio synthesizer.
- `screens.py`: `ScreenOverlay` win / capture end-of-game modals.
- `tutorial.py`: 5-scene onboarding sequence state machine.

---

## Complete Test Suite (`tests/`) ✅

| Test File | Covered Functionality | Status |
|---|---|---|
| `test_address.py` | Creation, wrapping, bit extraction, near-first formatting | ✅ PASSED |
| `test_ball.py` | Membership, hierarchy, topological relationship (6-bit exhaustive) | ✅ PASSED |
| `test_caretaker.py` | Detection ball, turn sequence | ✅ PASSED |
| `test_caretaker_m2.py` | Frustration widening, recognized layers | ✅ PASSED |
| `test_door.py` | ToggleDigit distance, AffineDoor isometry, even multiplier rejection | ✅ PASSED |
| `test_fiction.py` | Lineage tokens, door previews, echo descriptions, wing names | ✅ PASSED |
| `test_lure.py` | LureRegion timer, Caretaker lure attraction, UseLure action | ✅ PASSED |
| `test_metric.py` | 2-adic valuation, distance levels, 6-bit exhaustive strong triangle inequality | ✅ PASSED |
| `test_resources.py` | QuietSteps noise reduction, Chalking, BranchKey | ✅ PASSED |
| `test_tutorial.py` | Tutorial sequence advancement | ✅ PASSED |
| `test_world_generation.py` | Relational clues, multi-scale seal placement | ✅ PASSED |
| `test_world_m4.py` | 8-bit 5-seal world generation, Caretaker heat system | ✅ PASSED |
| `test_contraction.py` | $2\times$ contraction math & parity properties | ✅ PASSED |
| `test_rearrangement.py` | Distance-preserving affine rearrangement & contraction actions | ✅ PASSED |

**Total Automated Tests: 40 / 40 PASSED**

---

## Executable Entry Points

```bash
cd binary-house

# 4-bit 16-room tutorial scenario
python app.py --depth 4 --tutorial

# 6-bit 64-room stealth scenario with Caretaker
python app.py --depth 6

# Full 8-bit 256-room climax scenario
python app.py --depth 8

# Launch directly into F2 Mathematical Debug View
python app.py --depth 8 --debug
```
