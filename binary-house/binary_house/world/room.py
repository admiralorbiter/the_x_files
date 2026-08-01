from dataclasses import dataclass, field
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit

@dataclass(frozen=True)
class RoomStyle:
    """Inherited environmental style parameters derived from address prefix tree walking.
    
    Each field is determined by prefix mutations up to that digit depth.
    """
    architecture_family: int    # 0 or 1 from b₀
    floor_pattern: int          # 0 or 1 from b₁
    palette_index: int          # 0 or 1 from b₂
    ambient_sound_id: int       # 0 or 1 from b₃
    furniture_set: int          # 0 or 1 from b₄
    surface_texture: int        # 0 or 1 from b₅
    object_arrangement: int     # 0 or 1 from b₆
    anomaly_tag: int            # 0 or 1 from b₇


@dataclass
class Room:
    """Represents a single room in the 2-adic house."""
    address: Address
    style: RoomStyle
    doors: list[ToggleDigit] = field(default_factory=list)
    contains_seal: int | None = None          # Seal index (0, 1, 2) or None
    contains_resource: str | None = None      # "chalk", "quiet_steps", "branch_key", "address_lens"
    has_hiding_spot: bool = False
    environmental_clue: str | None = None
