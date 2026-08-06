import pytest
import numpy as np

from ovon.data.phenology import (
    get_species_phenology,
    get_weekly_species_weights,
    KC_SPECIES_PHENOLOGY_DATABASE
)

def test_indigo_bunting_phenology():
    prof = get_species_phenology("Indigo Bunting")
    assert prof.common_name == "Indigo Bunting"
    assert prof.migratory_status == "Neotropical Summer Resident"
    
    # May (Week 20) vs January (Week 3)
    ab_may = prof.weekly_abundance[19]  # week 20 (0-indexed 19)
    ab_jan = prof.weekly_abundance[2]   # week 3
    assert ab_may > 0.50
    assert ab_jan < 0.05

def test_dark_eyed_junco_phenology():
    prof = get_species_phenology("Dark-eyed Junco")
    # January (Week 3) vs July (Week 28)
    ab_jan = prof.weekly_abundance[2]
    ab_july = prof.weekly_abundance[27]
    assert ab_jan > 0.60
    assert ab_july < 0.05

def test_dynamic_weekly_weights():
    focal_species = ["Indigo Bunting", "Dark-eyed Junco", "House Finch"]
    
    # Week 20 (May spring migration) -> Indigo Bunting weighted higher than Junco
    weights_may = get_weekly_species_weights(focal_species, week=20)
    assert weights_may[0] > weights_may[1]  # Bunting > Junco

    # Week 3 (January winter) -> Junco weighted higher than Indigo Bunting
    weights_jan = get_weekly_species_weights(focal_species, week=3)
    assert weights_jan[1] > weights_jan[0]  # Junco > Bunting
