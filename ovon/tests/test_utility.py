import pytest
import numpy as np
from ovon.utility.metrics import (
    bernoulli_entropy,
    calculate_qbc_disagreement,
    spatial_habitat_kernel,
    standardize_features,
    StandardScaler
)

def test_standard_scaler():
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    scaler = StandardScaler()
    scaler.fit(X)
    X_std = scaler.transform(X)
    assert np.allclose(np.mean(X_std, axis=0), 0.0)
    assert np.allclose(np.std(X_std, axis=0), 1.0)

def test_spatial_habitat_kernel_validation():
    h1 = np.array([0.5, 0.2, 0.3])
    h2 = np.array([0.4, 0.1, 0.2, 0.8])
    with pytest.raises(ValueError, match="dimension mismatch"):
        spatial_habitat_kernel(0.0, 0.0, h1, 1.0, 1.0, h2)

def test_bernoulli_entropy():
    p = np.array([0.5, 0.0, 1.0])
    h = bernoulli_entropy(p)
    assert np.isclose(h[0], 1.0)
    assert np.isclose(h[1], 0.0, atol=1e-5)
    assert np.isclose(h[2], 0.0, atol=1e-5)
