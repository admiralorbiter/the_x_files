import numpy as np
import pytest

from ovon.utility.metrics import (
    bernoulli_entropy,
    calculate_qbc_disagreement,
    spatial_habitat_kernel,
    calculate_site_redundancy_to_history,
    compute_set_utility
)
from ovon.synthetic.generator import generate_synthetic_dataset

def test_bernoulli_entropy():
    # Entropy should be zero at boundary 0 and 1
    assert bernoulli_entropy(np.array([0.0]))[0] == pytest.approx(0.0, abs=1e-5)
    assert bernoulli_entropy(np.array([1.0]))[0] == pytest.approx(0.0, abs=1e-5)
    # Entropy should be 1.0 at p=0.5
    assert bernoulli_entropy(np.array([0.5]))[0] == pytest.approx(1.0, abs=1e-5)

def test_qbc_disagreement():
    # If all bootstrap models agree, disagreement should be ~0
    unanimous_preds = np.tile(np.array([0.7, 0.3])[:, np.newaxis], (1, 10))
    qbc_unanimous = calculate_qbc_disagreement(unanimous_preds)
    np.testing.assert_allclose(qbc_unanimous, 0.0, atol=1e-5)

    # If bootstrap models strongly disagree (50% predict 0.1, 50% predict 0.9)
    split_preds = np.array([
        [0.1] * 5 + [0.9] * 5,
        [0.2] * 5 + [0.8] * 5
    ])
    qbc_split = calculate_qbc_disagreement(split_preds)
    assert qbc_split[0] > 0.1
    assert qbc_split[1] > 0.1

def test_spatial_habitat_kernel():
    hab1 = np.array([0.5, 0.3, 0.2])
    hab2 = np.array([0.5, 0.3, 0.2])
    # Distance = 0 -> Kernel = 1.0
    k_0 = spatial_habitat_kernel(0.0, 0.0, hab1, 0.0, 0.0, hab2, spatial_length_km=10.0)
    assert k_0 == pytest.approx(1.0)

    # 3 km -> ~0.955
    k_3 = spatial_habitat_kernel(0.0, 0.0, hab1, 3.0, 0.0, hab2, spatial_length_km=10.0)
    assert 0.90 < k_3 < 0.98

    # 10 km -> ~0.606 (1/sqrt(e))
    k_10 = spatial_habitat_kernel(0.0, 0.0, hab1, 10.0, 0.0, hab2, spatial_length_km=10.0)
    assert 0.55 < k_10 < 0.65

    # 30 km -> < 0.02
    k_30 = spatial_habitat_kernel(0.0, 0.0, hab1, 30.0, 0.0, hab2, spatial_length_km=10.0)
    assert k_30 < 0.05

def test_set_utility_decay_on_duplicates():
    dataset = generate_synthetic_dataset(n_sites=5, seed=42)
    site = dataset.candidate_sites[0]

    # Single site utility
    u1 = compute_set_utility([site], dataset.existing_observations)

    # Duplicate site set (two identical sites)
    u2 = compute_set_utility([site, site], dataset.existing_observations, lambda_redundancy=1.0)

    # Adding a duplicate site should have lower marginal utility due to redundancy penalty
    assert u2 < 2.0 * u1
