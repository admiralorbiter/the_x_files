import pytest

from ovon.data.species_enrichment import (
    resolve_common_name,
    get_enriched_species_metadata,
    BIRD_SPECIES_TAXONOMY
)

def test_resolve_common_name():
    # Test scientific name to common name mapping
    assert resolve_common_name("Passerina cyanea") == "Indigo Bunting"
    assert resolve_common_name("Setophaga coronata") == "Yellow-rumped Warbler"
    assert resolve_common_name("Indigo Bunting") == "Indigo Bunting"

def test_get_enriched_species_metadata():
    meta = get_enriched_species_metadata("Indigo Bunting")
    assert meta.common_name == "Indigo Bunting"
    assert meta.scientific_name == "Passerina cyanea"
    assert meta.guild_class is not None
    assert meta.photo_url.startswith("http")
    assert len(meta.description) > 10
