import pytest
from binary_house.core.address import Address
from binary_house.core.door import ToggleDigit
from binary_house.ui.fiction import FictionMapper

def test_fiction_mapper_lineage():
    mapper = FictionMapper(depth=4)
    addr = Address(0b1010, depth=4)  # b0=0 (Wooden), b1=1 (Sun Wing), b2=0 (Candle), b3=1 (Moth)
    
    tokens = mapper.lineage_tokens(addr)
    assert tokens == ["Wooden", "Sun Wing", "Candle", "Moth"]
    assert mapper.lineage_str(addr) == "Wooden · Sun Wing · Candle · Moth"

def test_door_preview_fiction():
    mapper = FictionMapper(depth=4)
    addr = Address(0b0000, depth=4)
    door = ToggleDigit(3)  # Wardrobe (digit 3)
    
    prev = mapper.door_preview(door, addr, enable_caretaker=False)
    assert prev.door_object == "Wardrobe"
    assert prev.layer_name == "Memory"
    assert prev.kept_names == ["Foundation", "Wing", "Household"]
    assert prev.changed_name == "Memory"
    assert prev.noise == "Quiet"

def test_echo_descriptions():
    mapper = FictionMapper(depth=4)
    assert mapper.echo_str(None, 4) == "Right here"
    assert mapper.echo_str(3, 4) == "Almost identical — a single difference"
    assert mapper.echo_str(2, 4) == "Very close — same household"
    assert mapper.echo_str(0, 4) == "Other foundation entirely"
