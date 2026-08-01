from dataclasses import dataclass
from binary_house.game.state import GameState, TurnEvent

TUTORIAL_SCENES = [
    {
        "scene": 0,
        "title": "SCENE 1: THE WARDROBE",
        "instruction": "Click the Wardrobe door (digit 3). Notice how little the room changes.",
        "expected_digit": 3,
    },
    {
        "scene": 1,
        "title": "SCENE 2: THE FRONT DOOR",
        "instruction": "Now click the Front Door (digit 0). Notice how the entire room transforms!",
        "expected_digit": 0,
    },
    {
        "scene": 2,
        "title": "SCENE 3: HOUSE LINEAGE",
        "instruction": "Look at the ribbon above. The changed trait pulses while preserved traits stay bright.",
        "expected_digit": None,
    },
    {
        "scene": 3,
        "title": "SCENE 4: CARETAKER RECOGNITION",
        "instruction": "The Caretaker recognizes your Foundation and Wing! Choose a door that breaks its recognition.",
        "expected_digit": 1,
    },
    {
        "scene": 4,
        "title": "SCENE 5: THE EXIT WING",
        "instruction": "The exit is not a single location — it is ANY room inside the Moon Wing!",
        "expected_digit": None,
    },
]

@dataclass
class TutorialState:
    current_scene: int = 0
    completed: bool = False

    def get_current(self) -> dict | None:
        if self.completed or self.current_scene >= len(TUTORIAL_SCENES):
            return None
        return TUTORIAL_SCENES[self.current_scene]

    def advance(self, event: TurnEvent, state: GameState) -> bool:
        """Advance scene if action matches expectations. Returns True if scene advanced."""
        if self.completed:
            return False

        scene = self.get_current()
        if not scene:
            self.completed = True
            return False

        expected = scene["expected_digit"]
        if expected is None:
            # Auto advance on any valid turn
            self.current_scene += 1
            advanced = True
        elif event.move_scale == expected:
            self.current_scene += 1
            advanced = True
        else:
            advanced = False

        if self.current_scene >= len(TUTORIAL_SCENES):
            self.completed = True

        return advanced
