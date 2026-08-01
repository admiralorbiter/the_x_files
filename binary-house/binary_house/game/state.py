from dataclasses import dataclass, field
from typing import Literal
from collections import Counter
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.core.door import ToggleDigit, AffineDoor
from binary_house.core.contraction import contract_2x
from binary_house.core.metric import distance_level
from binary_house.world.room import Room
from binary_house.world.world import World
from binary_house.game.sound import SoundRegion
from binary_house.game.lure import LureRegion
from binary_house.game.caretaker import CaretakerState
from binary_house.game.player import PlayerAction, MoveAction, UseChalk, UseQuietSteps, UseLure, BranchKeyAction, RearrangeAction, ContractAction, WaitAction

@dataclass
class TurnEvent:
    turn: int
    player_before: Address
    player_after: Address
    move_scale: int | None
    sound_depth: int | None
    caretaker_before: Address
    caretaker_after: Address
    detected: bool
    description: str


@dataclass
class GameState:
    world: World
    player_address: Address
    caretaker: CaretakerState
    turn: int = 0
    seals_collected: set[int] = field(default_factory=set)
    sound_regions: list[SoundRegion] = field(default_factory=list)
    lure_regions: list[LureRegion] = field(default_factory=list)
    chalk_marks: dict[Ball, str] = field(default_factory=dict)
    resources: Counter[str] = field(default_factory=Counter)
    event_log: list[TurnEvent] = field(default_factory=list)
    phase: Literal["explore", "detected", "captured", "escaped", "won"] = "explore"
    enable_caretaker: bool = True  # Disabled for Milestone 1 tutorial mode

    @classmethod
    def create(cls, world: World, enable_caretaker: bool = True) -> "GameState":
        caretaker_search_root = Ball(residue=0, depth=0, total_depth=world.depth)
        caretaker = CaretakerState(
            address=world.caretaker_start,
            detection_depth=max(1, world.depth // 2),
            search_ball=caretaker_search_root,
        )
        return cls(
            world=world,
            player_address=world.player_start,
            caretaker=caretaker,
            enable_caretaker=enable_caretaker,
        )

    def rearrange_world(self, door: AffineDoor):
        """Apply distance-preserving affine permutation to all room addresses, player, caretaker, seals, exit, and chalk."""
        depth = self.world.depth
        
        # Remap all rooms
        new_rooms = {}
        for old_val, room in self.world.rooms.items():
            old_addr = Address(old_val, depth=depth)
            new_addr = door.apply(old_addr)
            new_room = Room(
                address=new_addr,
                style=room.style,
                doors=room.doors,
                contains_seal=room.contains_seal,
                contains_resource=room.contains_resource,
                has_hiding_spot=room.has_hiding_spot,
                environmental_clue=room.environmental_clue,
            )
            new_rooms[new_addr.value] = new_room
        self.world.rooms = new_rooms

        # Remap player & caretaker
        self.player_address = door.apply(self.player_address)
        self.caretaker.address = door.apply(self.caretaker.address)
        self.world.seal_locations = [door.apply(a) for a in self.world.seal_locations]

        # Remap exit ball
        new_exit_residue = door.apply(Address(self.world.exit_ball.residue, depth=depth)).value
        self.world.exit_ball = Ball(residue=new_exit_residue, depth=self.world.exit_ball.depth, total_depth=depth)

        # Remap chalk marks
        new_chalk = {}
        for ball, label in self.chalk_marks.items():
            new_res = door.apply(Address(ball.residue, depth=depth)).value
            new_chalk[Ball(residue=new_res, depth=ball.depth, total_depth=depth)] = label
        self.chalk_marks = new_chalk

    def apply_contraction(self):
        """Collapse the world via 2x contraction (x -> 2x mod 2^depth)."""
        self.player_address = contract_2x(self.player_address)
        self.caretaker.address = contract_2x(self.caretaker.address)
        self.caretaker.detection_depth = max(1, self.caretaker.detection_depth - 1)

    def step(self, action: PlayerAction) -> TurnEvent:
        """Execute a full turn sequence."""
        self.turn += 1
        p_before = self.player_address
        c_before = self.caretaker.address
        move_scale = None
        sound_depth = None
        desc = ""

        # 1. Player action
        if isinstance(action, MoveAction):
            door = action.door
            self.player_address = door.apply(self.player_address)
            move_scale = door.distance_level()
            sound_depth = door.noise_depth()
            desc = f"Moved through door (changed digit {move_scale}, distance 2^-{move_scale})"
            
            # Sound created
            sound_ball = Ball(
                residue=self.player_address.prefix(sound_depth),
                depth=sound_depth,
                total_depth=self.world.depth,
            )
            self.sound_regions.append(SoundRegion(ball=sound_ball))

        elif isinstance(action, UseQuietSteps):
            door = action.door
            self.player_address = door.apply(self.player_address)
            move_scale = door.distance_level()
            sound_depth = max(0, move_scale - 2)
            self.resources["quiet_steps"] -= 1
            desc = f"Used Quiet Steps through {door.index} passage"

        elif isinstance(action, UseChalk):
            ball = Ball(
                residue=self.player_address.prefix(action.depth),
                depth=action.depth,
                total_depth=self.world.depth,
            )
            self.chalk_marks[ball] = "Chalked"
            self.resources["chalk"] -= 1
            desc = f"Marked neighborhood depth {action.depth} with chalk"

        elif isinstance(action, UseLure):
            self.lure_regions.append(LureRegion(ball=action.lure_ball))
            self.resources["address_lens"] -= 1
            desc = f"Placed a lineage lure baiting the Caretaker"

        elif isinstance(action, BranchKeyAction):
            door = ToggleDigit(action.target_digit)
            self.player_address = door.apply(self.player_address)
            move_scale = door.distance_level()
            sound_depth = door.noise_depth()
            self.resources["branch_key"] -= 1
            desc = f"Used Branch Key to unlock passage digit {action.target_digit}"

        elif isinstance(action, RearrangeAction):
            self.rearrange_world(action.door)
            desc = f"The house rearranged ({action.name}). Distances were preserved!"

        elif isinstance(action, ContractAction):
            self.apply_contraction()
            desc = "The house folded inward (2x contraction)."

        elif isinstance(action, WaitAction):
            desc = "Waited quietly"

        # 2. Pick up items in current room
        current_room = self.world.rooms[self.player_address.value]
        if current_room.contains_seal is not None:
            self.seals_collected.add(current_room.contains_seal)
            current_room.contains_seal = None
            desc += " | Picked up a Seal!"

        if current_room.contains_resource:
            self.resources[current_room.contains_resource] += 1
            desc += f" | Found resource: {current_room.contains_resource}"
            current_room.contains_resource = None

        # 3. Sound & Lure region expansion & decay
        next_sounds = []
        for s in self.sound_regions:
            expanded = s.expand()
            if expanded:
                next_sounds.append(expanded)
        self.sound_regions = next_sounds

        next_lures = []
        for l in self.lure_regions:
            if l.tick():
                next_lures.append(l)
        self.lure_regions = next_lures

        # 4. Caretaker update & turn (if active)
        if self.enable_caretaker:
            self.caretaker.update_search(self.sound_regions, self.player_address, lure_regions=self.lure_regions)
            self.caretaker.act(self.world.depth)

            # Check detection & capture
            detected = self.caretaker.is_detecting(self.player_address)
            captured = self.player_address == self.caretaker.address

            if captured:
                self.phase = "captured"
                desc += " | CAPTURED by the Caretaker!"
            elif detected:
                self.phase = "detected"
                desc += " | Caretaker detects your presence in its neighborhood!"
            else:
                self.phase = "explore"
        else:
            detected = False

        # 5. Check win condition
        if self.world.exit_ball.contains(self.player_address) and len(self.seals_collected) >= len(self.world.seal_locations):
            self.phase = "won"
            desc += " | ESCAPED THE BINARY HOUSE!"

        event = TurnEvent(
            turn=self.turn,
            player_before=p_before,
            player_after=self.player_address,
            move_scale=move_scale,
            sound_depth=sound_depth,
            caretaker_before=c_before,
            caretaker_after=self.caretaker.address,
            detected=detected,
            description=desc,
        )
        self.event_log.append(event)
        return event
