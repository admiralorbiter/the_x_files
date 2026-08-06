import pytest
import numpy as np

from ovon.data.enviroatlas import (
    fetch_enviroatlas_covariates,
    covariates_to_habitat_vector,
    EnvironmentalCovariates,
    KC_LANDMARK_ENVIRONMENTAL_PROFILES
)
from ovon.data.fetch_urban import build_kc_urban_pedestrian_dataset

def test_fetch_enviroatlas_covariates():
    # Test curated landmark lookup
    covs = fetch_enviroatlas_covariates(39.0854, -94.5857, location_name="Union Station Plaza & Fountain")
    assert isinstance(covs, EnvironmentalCovariates)
    assert covs.impervious_surface_pct > 0.5
    assert covs.nlcd_class is not None

def test_covariates_to_habitat_vector():
    covs = EnvironmentalCovariates(
        tree_canopy_pct=0.60,
        impervious_surface_pct=0.10,
        distance_to_water_km=0.10,
        greenness_index=0.80,
        nlcd_class="Deciduous Forest Canopy"
    )
    vec = covariates_to_habitat_vector(covs)
    assert len(vec) == 4
    # Check L1 normalization
    assert pytest.approx(float(np.sum(vec)), 1e-4) == 1.0

def test_urban_dataset_has_environmental_covariates():
    dataset = build_kc_urban_pedestrian_dataset()
    site0 = dataset.candidate_sites[0]
    assert hasattr(site0, "env_covariates")
    assert site0.env_covariates is not None
    assert len(site0.habitat) == 4
