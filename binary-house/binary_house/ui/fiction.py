from dataclasses import dataclass
from typing import Literal
from binary_house.core.address import Address
from binary_house.core.ball import Ball
from binary_house.core.door import ToggleDigit
from binary_house.core.metric import distance_level
from binary_house.game.caretaker import CaretakerState

@dataclass(frozen=True)
class LayerInfo:
    index: int
    name: str           # "Foundation", "Wing", "Household", "Memory"
    state_0_name: str   # "Wooden"
    state_1_name: str   # "Stone"
    door_object: str    # "Front Door", "Stairwell", "Interior Door", "Wardrobe"

@dataclass(frozen=True)
class DoorPreview:
    door_object: str        # "Wardrobe"
    layer_name: str         # "Memory"
    kept_names: list[str]   # ["Foundation", "Wing", "Household"]
    changed_name: str       # "Memory"
    noise: str              # "Quiet", "Moderate", "LOUD — the Caretaker will hear"
    caretaker_still_detects: bool
    flavor: str             # "The room beyond remembers almost everything about this one."

# 4-bit and extended 8-bit layer metadata
LAYERS_4BIT = [
    LayerInfo(0, "Foundation", "Wooden", "Stone", "Front Door"),
    LayerInfo(1, "Wing", "Moon Wing", "Sun Wing", "Stairwell"),
    LayerInfo(2, "Household", "Candle", "Bell", "Interior Door"),
    LayerInfo(3, "Memory", "Eye", "Moth", "Wardrobe"),
]

LAYERS_EXTENDED = [
    LayerInfo(4, "Arrangement", "Mirror", "Clock", "Cabinet"),
    LayerInfo(5, "Surface", "Moss", "Ash", "Chest"),
    LayerInfo(6, "Object", "Portrait", "Letter", "Hatch"),
    LayerInfo(7, "Anomaly", "Silence", "Hum", "Trapdoor"),
]

class FictionMapper:
    """Translation layer mapping 2-adic mathematics to diegetic house fiction."""
    def __init__(self, depth: int = 8):
        self.depth = depth

    def layer(self, index: int) -> LayerInfo:
        if index < 4:
            return LAYERS_4BIT[index]
        elif index < 8:
            return LAYERS_EXTENDED[index - 4]
        else:
            return LayerInfo(index, f"Layer {index}", f"State 0 ({index})", f"State 1 ({index})", f"Door {index}")

    def trait_name(self, index: int, bit_val: int) -> str:
        info = self.layer(index)
        return info.state_0_name if bit_val == 0 else info.state_1_name

    def lineage_tokens(self, address: Address) -> list[str]:
        """Return list of trait names for the address, e.g. ['Wooden', 'Moon Wing', 'Candle', 'Eye']."""
        return [self.trait_name(i, address.bit(i)) for i in range(address.depth)]

    def lineage_str(self, address: Address) -> str:
        """Formatted lineage string."""
        return " · ".join(self.lineage_tokens(address))

    def echo_str(self, level: int | None, depth: int) -> str:
        """Translate 2-adic distance level to qualitative echo description."""
        if level is None:
            return "Right here"
        elif level >= depth - 1:
            return "Almost identical — a single difference"
        elif level >= depth - 2:
            return "Very close — same household"
        elif level >= max(1, depth // 2):
            return "Same wing"
        elif level == 1:
            return "Same foundation, different branch"
        else:
            return "Other foundation entirely"

    def door_preview(
        self,
        door: ToggleDigit,
        from_addr: Address,
        caretaker: CaretakerState | None = None,
        enable_caretaker: bool = True,
    ) -> DoorPreview:
        to_addr = door.apply(from_addr)
        digit_idx = door.index
        layer_info = self.layer(digit_idx)

        kept_names = [self.layer(i).name for i in range(digit_idx)]
        changed_name = layer_info.name

        # Noise level
        if digit_idx == 0:
            noise = "LOUD — the Caretaker will hear this"
        elif digit_idx < 3:
            noise = "Moderate"
        else:
            noise = "Quiet"

        # Caretaker detection status after move
        still_detects = False
        if enable_caretaker and caretaker is not None:
            still_detects = caretaker.is_detecting(to_addr)

        # Flavor text
        if digit_idx == 0:
            flavor = "Nothing beyond belongs to this part of the house."
        elif digit_idx == 1:
            flavor = "Leads to the counterpart wing of the foundation."
        elif digit_idx == 2:
            flavor = "Leads to a paired household within this wing."
        else:
            flavor = "The room beyond remembers almost everything about this one."

        return DoorPreview(
            door_object=layer_info.door_object,
            layer_name=layer_info.name,
            kept_names=kept_names,
            changed_name=changed_name,
            noise=noise,
            caretaker_still_detects=still_detects,
            flavor=flavor,
        )

    def post_move_flavor(self, from_addr: Address, to_addr: Address) -> str:
        k = distance_level(from_addr, to_addr)
        if k is None:
            return "You remained in place."
        elif k == 0:
            return "This part of the house has never known you."
        elif k == 1:
            return "The wing remembers nothing of where you were."
        elif k == 2:
            return "The furniture belongs to a different family."
        else:
            return "The floor plan remembers you, but one detail has changed."

    def caretaker_recognition_str(self, caretaker: CaretakerState, player: Address) -> str:
        """Return fiction description of Caretaker's detection ball."""
        h = caretaker.detection_depth
        matching_traits = [self.trait_name(i, player.bit(i)) for i in range(min(h, player.depth))]
        return f"Searching: {' · '.join(matching_traits)}"

    def wing_name(self, ball: Ball) -> str:
        """Return diegetic name of an Ultrametric Ball (e.g. 'The Wooden Moon Wing')."""
        if ball.depth == 0:
            return "The Entire House"
        traits = [self.trait_name(i, (ball.residue >> i) & 1) for i in range(min(ball.depth, self.depth))]
        return f"The {' '.join(traits)}"
