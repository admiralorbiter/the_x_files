import pytest
import numpy as np

from ovon.features.grid import EqualAreaGrid
from ovon.features.redundancy import RedundancyAtlas

def test_equal_area_grid_creation():
    grid = EqualAreaGrid(center_lat=39.0997, center_lon=-94.5786, radius_km=30.0, resolution_km=3.0)
    assert grid.total_cells > 0
    assert grid.n_rows == grid.n_cols
    cell_0 = grid.get_cell(0)
    assert cell_0.area_sq_km == pytest.approx(9.0)

def test_point_assignment():
    grid = EqualAreaGrid(center_lat=39.0997, center_lon=-94.5786, radius_km=30.0, resolution_km=3.0)
    # Center point should map to a valid central cell_id
    center_cell = grid.assign_point(39.0997, -94.5786)
    assert center_cell is not None
    assert 0 <= center_cell < grid.total_cells

    # Point far outside should return None
    outside_cell = grid.assign_point(10.0, 10.0)
    assert outside_cell is None

def test_multiscale_habitat_features():
    grid = EqualAreaGrid()
    features = grid.extract_multiscale_habitat_features(cell_id=5, buffers_m=(500, 1500, 3000))
    assert "habitat_buffer_500m" in features
    assert "habitat_buffer_1500m" in features
    assert "habitat_buffer_3000m" in features
    # Check probabilities sum to 1.0
    np.testing.assert_allclose(np.sum(features["habitat_buffer_500m"]), 1.0, atol=1e-4)

def test_redundancy_atlas():
    grid = EqualAreaGrid(radius_km=20.0, resolution_km=5.0)
    atlas = RedundancyAtlas(grid)

    obs = [
        {"lat": 39.0997, "lon": -94.5786, "week": 18, "observer_id": "obs1", "habitat": np.array([0.5, 0.3, 0.2])},
        {"lat": 39.0997, "lon": -94.5786, "week": 18, "observer_id": "obs2", "habitat": np.array([0.5, 0.3, 0.2])}
    ]
    atlas.ingest_observations(obs)
    top_undersampled = atlas.get_top_undersampled_cells(week=18, top_k=5)
    assert len(top_undersampled) == 5
