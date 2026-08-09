import pytest
from pathlib import Path
from impact.datasets.scruples import ScruplesAdapter
from impact.datasets.base import calculate_binary_entropy


def test_scruples_starter_loading(tmp_path):
    adapter = ScruplesAdapter(data_dir=tmp_path)
    scenarios = adapter.load_or_fetch()
    assert len(scenarios) >= 5
    for s in scenarios:
        assert s.human_prob_a + s.human_prob_b == pytest.approx(1.0)
        assert s.human_entropy >= 0.0


def test_entropy_calculation():
    # p=0.5 -> 1.0 bit entropy
    assert calculate_binary_entropy(0.5, 0.5) == pytest.approx(1.0)
    # p=1.0 -> 0.0 bit entropy
    assert calculate_binary_entropy(1.0, 0.0) == pytest.approx(0.0)
