import random
from dataclasses import dataclass
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.world.room import Room
from binary_house.world.generator import generate_room_style, generate_room_doors

@dataclass
class World:
    """The complete 2-adic world graph of 2^depth rooms."""
    depth: int
    seed: int
    rooms: dict[int, Room]
    seal_locations: list[Address]
    exit_ball: Ball
    caretaker_start: Address
    player_start: Address


def generate_world(depth: int = 8, seed: int = 42) -> World:
    """Generate a deterministic 2-adic world populated with rooms, seals, and resources."""
    num_rooms = 1 << depth
    rng = random.Random(seed)

    rooms: dict[int, Room] = {}
    for v in range(num_rooms):
        addr = Address(v, depth=depth)
        style = generate_room_style(addr, seed)
        doors = generate_room_doors(addr, seed)
        rooms[v] = Room(address=addr, style=style, doors=doors)

    # Place player start and caretaker start in distant branches (differing at bit 0)
    player_start = Address(0, depth=depth)
    caretaker_start = Address((1 << depth) - 1, depth=depth)  # opposite end

    # Place 3 seals across different depth balls
    seal_locations = [
        Address(rng.randint(0, (1 << (depth - 1)) - 1), depth=depth),
        Address(rng.randint(1 << (depth - 1), (1 << depth) - 1), depth=depth),
        Address(rng.randint(0, (1 << depth) - 1), depth=depth),
    ]

    for idx, s_addr in enumerate(seal_locations):
        room = rooms[s_addr.value]
        room.contains_seal = idx
        
        # Environmental relational clue
        if idx == 0:
            room.environmental_clue = "The Local Seal rests in a room sharing your foundation and wing."
        elif idx == 1:
            room.environmental_clue = "The Branch Seal rests in a room sharing your foundation, but not your wing."
        else:
            room.environmental_clue = "The Root Seal rests in a room with a completely different foundation."

    # Define exit ball (e.g. depth-4 ball around a target residue)
    exit_residue = rng.randint(0, (1 << max(1, depth // 2)) - 1)
    exit_ball = Ball(residue=exit_residue, depth=max(1, depth // 2), total_depth=depth)

    # Scatter resources
    resources = ["chalk", "quiet_steps", "branch_key", "address_lens"]
    resource_addrs = rng.sample(list(rooms.values()), k=min(8, num_rooms))
    for r_room, r_name in zip(resource_addrs, resources * 2):
        r_room.contains_resource = r_name

    return World(
        depth=depth,
        seed=seed,
        rooms=rooms,
        seal_locations=seal_locations,
        exit_ball=exit_ball,
        caretaker_start=caretaker_start,
        player_start=player_start,
    )
