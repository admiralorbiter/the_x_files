import random
from dataclasses import dataclass
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.core.metric import distance_level
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


def make_relational_clue(seal_addr: Address, player_start: Address, depth: int) -> str:
    """Generate a diegetic clue describing a seal's location relative to the player start."""
    from binary_house.ui.fiction import FictionMapper
    mapper = FictionMapper(depth)
    k = distance_level(seal_addr, player_start)
    if k is None:
        return "The seal rests right here, in this very room."
    if k == 0:
        return "The Root Seal rests in a room with a completely different Foundation."
    
    kept = [mapper.layer(i).name for i in range(k)]
    changed_layer = mapper.layer(k)
    changed_state = mapper.trait_name(k, seal_addr.bit(k))
    
    kept_str = " and ".join(kept)
    return f"The seal shares your {kept_str}, but its {changed_layer.name} is {changed_state}."


def _place_seal_at_distance(rng: random.Random, player_start: Address, target_level: int, depth: int) -> Address:
    """Generate an address that differs from player_start at exactly digit target_level."""
    flipped_bit = player_start.bit(target_level) ^ 1
    
    # Keep low-order bits up to target_level - 1 identical to player_start
    val = 0
    for i in range(target_level):
        val |= (player_start.bit(i) << i)
    
    # Set the target_level bit to flipped_bit
    val |= (flipped_bit << target_level)
    
    # Randomize deeper bits (from target_level + 1 to depth - 1)
    for i in range(target_level + 1, depth):
        random_bit = rng.randint(0, 1)
        val |= (random_bit << i)
        
    return Address(val, depth=depth)


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

    player_start = Address(0, depth=depth)
    caretaker_start = Address((1 << depth) - 1, depth=depth)

    # Place seals across distinct distance levels from player_start:
    # 4-bit world: 3 seals [0, 2, 3]
    # 6-bit world: 3 seals [0, 3, 5]
    # 8-bit world: 5 seals [0, 1, 3, 5, 7]
    if depth >= 8:
        seal_levels = [0, 1, 3, 5, 7]
    else:
        seal_levels = [0, max(1, depth // 2), depth - 1]

    seal_locations = [_place_seal_at_distance(rng, player_start, lvl, depth) for lvl in seal_levels]

    for idx, s_addr in enumerate(seal_locations):
        room = rooms[s_addr.value]
        room.contains_seal = idx
        room.environmental_clue = make_relational_clue(s_addr, player_start, depth)

    # Define exit ball (e.g. depth-4 or depth // 2 ball around target residue)
    exit_depth = max(1, depth // 2)
    exit_residue = rng.randint(0, (1 << exit_depth) - 1)
    exit_ball = Ball(residue=exit_residue, depth=exit_depth, total_depth=depth)

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
