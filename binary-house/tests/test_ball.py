import pytest
from binary_house.core.address import Address
from binary_house.core.ball import Ball

def test_ball_contains():
    # Ball at depth 3 with fixed prefix 0b101 (5)
    ball = Ball(residue=0b101, depth=3, total_depth=8)
    
    # Address with prefix 0b101 (bits 0,1,2 = 1,0,1)
    addr_inside = Address(0b11001101, depth=8)  # bits 0..2 = 1,0,1 -> 5
    addr_outside = Address(0b11001011, depth=8)  # bits 0..2 = 1,1,0 -> 3
    
    assert ball.contains(addr_inside)
    assert not ball.contains(addr_outside)

def test_ball_hierarchy():
    root = Ball(residue=0, depth=0, total_depth=8)
    assert root.parent() is None
    assert root.size() == 256

    child0, child1 = root.children()
    assert child0.depth == 1
    assert child0.residue == 0
    assert child1.depth == 1
    assert child1.residue == 1
    assert child0.size() == 128
    assert child1.size() == 128

def test_ball_relationships():
    b1 = Ball(residue=0b01, depth=2, total_depth=8)
    b2 = Ball(residue=0b01, depth=2, total_depth=8)
    b3 = Ball(residue=0b11, depth=2, total_depth=8)
    b_parent = Ball(residue=0b1, depth=1, total_depth=8)

    assert Ball.relationship(b1, b2) == "equal"
    assert Ball.relationship(b1, b3) == "disjoint"
    assert Ball.relationship(b1, b_parent) == "nested"

def test_exhaustive_ball_relationships_6bit():
    # Test that all pairs of balls in a 6-bit space are either equal, nested, or disjoint (never partial overlap)
    total_depth = 6
    balls = []
    for d in range(total_depth + 1):
        num_residues = 1 << d
        for r in range(num_residues):
            balls.append(Ball(residue=r, depth=d, total_depth=total_depth))

    for i, b_a in enumerate(balls):
        for b_b in balls[i:]:
            rel = Ball.relationship(b_a, b_b)
            assert rel in ("equal", "nested", "disjoint")

            # Double-check against actual element sets
            addrs = [Address(v, depth=total_depth) for v in range(1 << total_depth)]
            set_a = {a for a in addrs if b_a.contains(a)}
            set_b = {a for a in addrs if b_b.contains(a)}

            if rel == "equal":
                assert set_a == set_b
            elif rel == "nested":
                assert set_a.issubset(set_b) or set_b.issubset(set_a)
            elif rel == "disjoint":
                assert set_a.isdisjoint(set_b)
