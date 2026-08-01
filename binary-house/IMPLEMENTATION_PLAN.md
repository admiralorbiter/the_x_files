# The Binary House — Implementation Plan

A turn-based puzzle-stealth prototype built in Python + Pygame, in which all spatial relationships, enemy detection, sound propagation, and puzzle logic are grounded in 2-adic (ultrametric) distance.

The prototype is simultaneously a game and a mathematical interface-design experiment.

---

## Decisions & Resolved Questions

> [!NOTE]
> **Visual representation style** — **Decision: Abstract card/tile view for M0–M2**.
> Rooms are rendered as abstract tiles where visual layers (color family, hatch pattern, icon) encode address prefix depth. This provides maximal legibility for testing the 2-adic distance mental model before upgrading to diegetic rendering in Milestone 4.

> [!NOTE]
> **Audio inheritance** — **Decision: Minimal synthesized audio in Milestone 1**.
> Pygame's `sndarray` (or simple numpy waveform synthesis) will synthesize simple additive audio layers for digits 0–2. Rooms sharing near digits share sonic layers, testing multi-channel inheritance early without asset overhead.

> [!NOTE]
> **Progressive disclosure world sizes** — Parameterized via `--depth` (4 for M1, 6 for M2/M3, 8 for M4). All stages run on the same codebase.

---

## Proposed Changes

### Component 1 — Project Scaffold

#### [NEW] `binary-house/requirements.txt`
- `pygame>=2.5`
- `pytest>=8.0`
- `pytest-cov`

#### [NEW] `binary-house/app.py`
Top-level entry point. Parses a `--depth` flag (default 8), initializes `pygame`, constructs `World` and `GameState`, and hands control to the main game loop.

#### [NEW] `binary-house/IMPLEMENTATION_PLAN.md`
Copy of this document, living inside the project folder for posterity.

---

### Component 2 — Mathematical Kernel (`binary_house/core/`)

This is the most critical component. It must be 100% tested before any rendering begins (Milestone 0 stop condition).

#### [NEW] `binary_house/core/address.py`

```python
@dataclass(frozen=True)
class Address:
    value: int      # integer in [0, 2**depth)
    depth: int = 8

    def bit(self, index: int) -> int:
        """Return the digit at near-position `index` (0 = least significant)."""
        return (self.value >> index) & 1

    def prefix(self, k: int) -> int:
        """Return the integer formed by the first k near digits."""
        return self.value & ((1 << k) - 1)

    def near_first_str(self) -> str:
        """Format as b₀·b₁·…·b_{depth-1}."""
        return " · ".join(str(self.bit(i)) for i in range(self.depth))
```

#### [NEW] `binary_house/core/metric.py`

```python
def valuation_2(n: int) -> int:
    """2-adic valuation of a nonzero integer."""
    ...

def distance_level(a: Address, b: Address) -> int | None:
    """Index of first differing near digit; None if identical.
    
    The 2-adic distance is 2^(-distance_level(a, b)).
    Game systems should work with the integer level, not the float.
    """
    ...

def distance_float(a: Address, b: Address) -> float:
    """2^(-distance_level(a,b)), or 0.0 if identical. For display only."""
    ...
```

Key invariant tested exhaustively:
- `distance_level(x, x XOR 2^k) == k` for all valid x, k
- Strong triangle inequality: `distance_level(x,z) >= min(distance_level(x,y), distance_level(y,z))`

#### [NEW] `binary_house/core/ball.py`

```python
@dataclass(frozen=True)
class Ball:
    residue: int   # the shared prefix value
    depth: int     # number of fixed digits (0 = whole space)

    def contains(self, address: Address) -> bool: ...
    def size(self) -> int: ...          # 2^(address_depth - self.depth)
    def parent(self) -> Ball | None: ... # Ball at depth-1
    def children(self) -> tuple[Ball, Ball]: ... # two sub-balls at depth+1

    @staticmethod
    def relationship(a: "Ball", b: "Ball") -> Literal["equal","nested","disjoint"]: ...
```

Key invariant: two balls are always `equal`, one `nested` inside the other, or `disjoint`. Never partial overlap.

#### [NEW] `binary_house/core/door.py`

```python
class DoorOperation(Protocol):
    def apply(self, address: Address) -> Address: ...
    def distance_level(self) -> int: ...        # how large a move this is
    def noise_depth(self) -> int: ...           # ball depth of initial sound

@dataclass(frozen=True)
class ToggleDigit:
    index: int   # digit to flip (0 = nearest)
    def apply(self, address: Address) -> Address:
        return Address(address.value ^ (1 << self.index), address.depth)
    def distance_level(self) -> int: return self.index
    def noise_depth(self) -> int: return self.index   # noise fills ball at this depth

@dataclass(frozen=True)
class AffineDoor:
    """x → (multiplier * x + offset) mod 2^depth. Used for Milestone 5."""
    multiplier: int   # must be odd
    offset: int
    def apply(self, address: Address) -> Address: ...
```

---

### Component 3 — World Model (`binary_house/world/`)

#### [NEW] `binary_house/world/room.py`

```python
@dataclass
class RoomStyle:
    architecture_family: int    # 0/1 from b₀
    floor_pattern: int          # 0/1 from b₁
    palette_index: int          # 0/1 from b₂
    ambient_sound_id: int       # 0/1 from b₃
    furniture_set: int          # 0/1 from b₄
    surface_texture: int        # 0/1 from b₅
    object_arrangement: int     # 0/1 from b₆
    anomaly_tag: int            # 0/1 from b₇

@dataclass
class Room:
    address: Address
    style: RoomStyle
    doors: list[ToggleDigit]        # available exits
    contains_seal: int | None       # seal index 0/1/2, or None
    contains_resource: str | None   # "chalk" | "quiet_steps" | "branch_key" | "address_lens"
    has_hiding_spot: bool
    environmental_clue: str | None  # text clue for Address Reconstruction puzzles
```

#### [NEW] `binary_house/world/generator.py`

Seeded prefix-tree room generator. Each room's `RoomStyle` is built by walking the address from the root, applying one controlled mutation per digit:

```python
def room_style(address: Address, world_seed: int) -> RoomStyle:
    style = base_style(world_seed)
    prefix = 0
    for depth in range(address.depth):
        prefix |= address.bit(depth) << depth
        style = mutate_style(style, seed=hash((world_seed, depth, prefix)), depth=depth)
    return style
```

This guarantees **shared-prefix → shared-style** without explicit lookup tables.

Door availability is also seeded: every room always has two to four doors covering a spread of digit scales. Mandatory doors at digit 0 (structural) and digit `depth-1` (deepest) are always present.

#### [NEW] `binary_house/world/world.py`

```python
@dataclass
class World:
    depth: int          # 4, 6, or 8
    seed: int
    rooms: dict[int, Room]          # address.value → Room
    seal_locations: list[Address]   # 3 seals for full prototype
    exit_ball: Ball                 # the target neighborhood
    caretaker_start: Address
    player_start: Address
```

Populated once at startup. Immutable after generation.

---

### Component 4 — Game Logic (`binary_house/game/`)

#### [NEW] `binary_house/game/state.py`

```python
@dataclass
class GameState:
    world: World
    player_address: Address
    caretaker: CaretakerState
    turn: int
    seals_collected: set[int]
    sound_regions: list[SoundRegion]    # active sound balls with decay timers
    resources: Counter[str]
    event_log: list[TurnEvent]
    phase: Literal["explore","detected","captured","escaped","won"]
```

The `step(action)` method executes the full **turn sequence**:
1. Player movement resolves (address change, resource use)
2. New `SoundRegion` created at `Ball(residue=new_addr.prefix(door.distance_level()), depth=door.distance_level())`
3. All `SoundRegion`s expand one level (depth decreases by 1)
4. Caretaker updates belief ball (narrows if sound/door evidence available)
5. Caretaker acts (moves toward player belief)
6. Detection check: `player_address ≡ caretaker_address (mod 2^h)`
7. Capture check: `player_address == caretaker_address`
8. Seal pickup check
9. Exit check: `exit_ball.contains(player_address)` and all seals collected
10. Append `TurnEvent` to log

#### [NEW] `binary_house/game/caretaker.py`

```python
@dataclass
class CaretakerState:
    address: Address
    detection_depth: int     # h — detects player within this ball
    search_ball: Ball        # current known player region
    suspicion: int           # 0–100
    movement_energy: int
```

Deterministic behavior per turn:
- If `search_ball.depth < detection_depth + 2`: narrow search one level
- Else: move to any address inside `search_ball` at minimum cost
- Movement cost of changing digit `k` = `(address.depth - k)` — prefers local moves

#### [NEW] `binary_house/game/sound.py`

```python
@dataclass
class SoundRegion:
    ball: Ball
    age: int = 0

    def expand(self) -> "SoundRegion | None":
        """Return parent ball region, or None if already at root."""
        parent = self.ball.parent()
        if parent is None:
            return None
        return SoundRegion(ball=parent, age=self.age + 1)
```

Caretaker receives a "sound signal" when its address is inside any active `SoundRegion`. It uses this to narrow its `search_ball`.

#### [NEW] `binary_house/game/player.py`

Resource management and action validation. Actions: `MoveAction(door)`, `UseChalk(depth)`, `UseQuietSteps(door)`, `UseBranchKey(door)`, `UseAddressLens()`, `Wait()`.

---

### Component 5 — UI (`binary_house/ui/`)

**Milestone 1 scope**: abstract node/card view. Diegetic room rendering deferred to Milestone 4.

#### [NEW] `binary_house/ui/renderer.py`

Main Pygame surface compositor. Layout:

```
┌──────────────────────────────────────────────────────┐
│  ADDRESS RIBBON                                      │
├────────────────┬─────────────────────┬───────────────┤
│ NEIGHBORHOOD   │   ROOM PANEL        │ SCALE LEDGER  │
│ STACK          │                     │               │
│                │  (visual style +    │  DISTANCE 2⁻⁷ │
│ 1·0·1·1·...    │   door list)        │  • faint sound│
│                │                     │               │
│                │                     │  DISTANCE 2⁻⁴ │
│                │                     │  • seal       │
├────────────────┴─────────────────────┴───────────────┤
│  DOOR PREVIEW   (inline, updates on hover/select)    │
└──────────────────────────────────────────────────────┘
```

#### [NEW] `binary_house/ui/hud.py`

- **Address ribbon**: `b₀ · b₁ · … · b₇`. The selected door's changed digit pulses; preserved digits stay bright; deeper unaffected digits dimmed.
- **Neighborhood stack**: rows of `"1·0·1·1·…"` with room count, known threats, known objectives.
- **Scale ledger**: entities grouped by distance level. **No angular position is implied**.
- **Door preview**: shows current address → result, changed digit index, distance, noise level.

#### [NEW] `binary_house/ui/assets.py`

Procedural visual generation. Each `RoomStyle` field maps to a distinct visual parameter (shape family, hatch pattern, color hue, icon). Abstract card view for early milestones. All digit state encoded with *both* color/hue *and* shape/pattern (accessibility requirement).

---

### Component 6 — Tests (`tests/`)

#### [NEW] `tests/test_address.py`
- Bit extraction correctness
- `near_first_str` formatting
- Prefix extraction

#### [NEW] `tests/test_metric.py`
- `distance_level(x, x ^ 2^k) == k` for all x in 6-bit world, all k
- Strong triangle inequality: exhaustive 64³ = 262,144 triple check
- Symmetry: `distance_level(a,b) == distance_level(b,a)`
- Identity: `distance_level(a,a) is None`

#### [NEW] `tests/test_ball.py`
- Membership correctness
- Nested-or-disjoint: exhaustive check over all ball pairs in 6-bit world
- `parent().contains(x)` if `child.contains(x)`

#### [NEW] `tests/test_door.py`
- `ToggleDigit(k).apply(x)` has `distance_level == k`
- `AffineDoor(a, b)` with odd `a` is an isometry
- Translation `AffineDoor(1, b)` is an isometry for all b

#### [NEW] `tests/test_caretaker.py`
- Detection fires iff `player_address.prefix(h) == caretaker_address.prefix(h)`
- Search ball narrows correctly on sound signal
- Movement cost ordering: local moves preferred over structural

#### [NEW] `tests/test_sound.py`
- Sound region expands through parent balls
- After `depth` expansions, sound covers the whole space

---

## Verification Plan

### Automated Tests (Milestone 0 gate)

```bash
cd binary-house
pytest tests/ -v --tb=short
```

All tests must pass before renderer work begins. The mathematical kernel is treated as a safety-critical component.

Exhaustive invariants checked on the **6-bit world** (64 addresses):

| Invariant | Scope |
|-----------|-------|
| `d(x, x XOR 2^k) = 2^(−k)` | all 64 × 8 pairs |
| Strong triangle inequality | 64³ = 262,144 triples |
| Balls nested or disjoint | all ball pairs |
| Translation isometry | all 64 × 64 (x,b) pairs |
| Odd-multiplier isometry | all 32 odd multipliers × 64 addresses |

### Manual Verification (per milestone)

| Milestone | Check |
|-----------|-------|
| M1 | Player can identify which door makes the smallest move without coaching |
| M1 | Room similarity visibly correlates with shared prefix length |
| M2 | Player navigates to a target ball from a partial address description |
| M3 | Player correctly predicts Caretaker detection before it fires |
| M3 | Player escapes by changing exactly the correct digit scale |
| M4 | 80%+ correct proximity ranking after 10 minutes of play |
| M5 | Player notices distances unchanged after house transformation |

---

## Risk Notes

| Risk | Mitigation in this plan |
|------|------------------------|
| Feels like a menu, not a world | Abstract card view is explicitly a scaffold; diegetic rendering targeted for M4 |
| Binary notation dominates | Environmental style inheritance is the *primary* teaching mechanism; digits appear secondarily |
| Random toggling solves everything | Limited door availability per room + noise cost + Caretaker create meaningful pressure |
| Caretaker obscures learning | M1 has no Caretaker; M3 Caretaker has fully visible detection ball and deterministic preview |
| Finite-approximation confusion | `AffineDoor` / contraction mechanics gated behind M5; not in core loop |
| Euclidean false interpretation | Scale ledger uses *no angular placement*; neighborhood stack uses containment language only |
