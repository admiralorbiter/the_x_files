import random
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit
from binary_house.world.room import RoomStyle

def generate_room_style(address: Address, world_seed: int) -> RoomStyle:
    """Generate RoomStyle using seeded prefix tree mutation.
    
    Guarantees that rooms sharing a long prefix inherit identical early style decisions.
    """
    style_bits = []
    prefix = 0
    for depth in range(address.depth):
        bit_val = address.bit(depth)
        prefix |= (bit_val << depth)
        
        # Seed generator deterministically with (world_seed, depth, prefix)
        rng = random.Random(hash((world_seed, depth, prefix)))
        style_bits.append(rng.randint(0, 1))

    # Pad style_bits up to 8 fields if address.depth < 8
    while len(style_bits) < 8:
        style_bits.append(0)

    return RoomStyle(
        architecture_family=style_bits[0],
        floor_pattern=style_bits[1],
        palette_index=style_bits[2],
        ambient_sound_id=style_bits[3],
        furniture_set=style_bits[4],
        surface_texture=style_bits[5],
        object_arrangement=style_bits[6],
        anomaly_tag=style_bits[7],
    )


def generate_room_doors(address: Address, world_seed: int) -> list[ToggleDigit]:
    """Generate available doors for a room.
    
    Guarantees:
    1. Structural door (index 0 - flips b₀) is always present.
    2. Deepest door (index depth-1 - flips b_{depth-1}) is always present.
    3. 1 to 2 additional scale doors selected deterministically.
    """
    doors = [ToggleDigit(0), ToggleDigit(address.depth - 1)]
    
    rng = random.Random(hash((world_seed, "doors", address.value)))
    available_indices = [i for i in range(1, address.depth - 1)]
    if available_indices:
        num_extra = min(len(available_indices), rng.randint(1, 2))
        extra_indices = rng.sample(available_indices, num_extra)
        for idx in extra_indices:
            doors.append(ToggleDigit(idx))

    # Sort doors by scale index
    doors.sort(key=lambda d: d.index)
    return doors
