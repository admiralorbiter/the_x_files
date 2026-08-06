import requests
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class TaxonRef:
    """
    Canonical taxon identifier reference bridging common names and scientific binomials.
    Prevents cross-platform mismatch between GBIF, eBird, and iNaturalist evidence.
    """
    taxon_id: str
    scientific_name: str
    common_name: str

@dataclass
class SpeciesMetadata:
    common_name: str
    scientific_name: str
    guild_class: str
    primary_habitat: str
    photo_url: str
    description: str
    conservation_status: str = "Least Concern (IUCN)"
    wikipedia_url: str = ""

# Curated Master Taxonomy & Habitat Dictionary for Kansas City Focal Species
BIRD_SPECIES_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "Indigo Bunting": {
        "scientific_name": "Passerina cyanea",
        "guild": "Migratory Seed-Eater / Granivore",
        "habitat": "Urban Edges, Shrublands & Park Glades",
        "description": "A vibrant blue migratory songbird that nests in brushy field edges, suburban parks, and restoration corridors.",
        "wikipedia_slug": "Indigo_bunting"
    },
    "Yellow-rumped Warbler": {
        "scientific_name": "Setophaga coronata",
        "guild": "Migratory Insectivore",
        "habitat": "Tree Canopy & Wooded Urban Parks",
        "description": "Abundant migratory warbler recognizable by its bright yellow rump patch, foraging actively in mature park canopy.",
        "wikipedia_slug": "Yellow-rumped_warbler"
    },
    "Belted Kingfisher": {
        "scientific_name": "Megaceryle alcyon",
        "guild": "Resident Riparian Piscivore",
        "habitat": "Lakeshores, Ponds & Creek Corridors",
        "description": "Stocky blue-gray waterbird with a shaggy crest, perching along urban ponds, Brush Creek, and Missouri River banks.",
        "wikipedia_slug": "Belted_kingfisher"
    },
    "Bald Eagle": {
        "scientific_name": "Haliaeetus leucocephalus",
        "guild": "Resident Apex Raptor",
        "habitat": "Large Riverfronts, Reservoirs & Floodplains",
        "description": "Iconic large raptor nesting near major Missouri and Kansas river corridors, Smithville Lake, and Jacomo wetlands.",
        "wikipedia_slug": "Bald_eagle"
    },
    "Northern Cardinal": {
        "scientific_name": "Cardinalis cardinalis",
        "guild": "Resident Granivore",
        "habitat": "Neighborhood Backyards, Thickets & Parks",
        "description": "Bright red year-round songbird with a clear whistle, common across all urban and suburban green spaces.",
        "wikipedia_slug": "Northern_cardinal"
    },
    "Blue Jay": {
        "scientific_name": "Cyanocitta cristata",
        "guild": "Resident Omnivore / Seed Disperser",
        "habitat": "Wooded Neighborhoods, Oak Canopy & Parks",
        "description": "Intelligent, vocal jay key to acorn dispersal across mature Kansas City oak-hickory urban forest patches.",
        "wikipedia_slug": "Blue_jay"
    },
    "Red-tailed Hawk": {
        "scientific_name": "Buteo jamaicensis",
        "guild": "Resident Buteo Raptor",
        "habitat": "Open Fields, Highway Corridors & Parks",
        "description": "Large soaring hawk frequently perching on highway light poles, tree edges, and open park meadows.",
        "wikipedia_slug": "Red-tailed_hawk"
    },
    "Tufted Titmouse": {
        "scientific_name": "Baeolophus bicolor",
        "guild": "Resident Cavity-Nesting Insectivore",
        "habitat": "Mature Tree Canopy & Wooded Parks",
        "description": "Small gray crested bird with rusty flanks, vocalizing actively in mature urban tree canopies.",
        "wikipedia_slug": "Tufted_titmouse"
    },
    "Chimney Swift": {
        "scientific_name": "Chaetura pelagica",
        "guild": "Migratory Aerial Insectivore",
        "habitat": "Masonry Chimneys & Urban Skylines",
        "description": "Cigar-shaped aerial insectivore roosting in brick chimneys across historic Downtown, Midtown, and Westport.",
        "wikipedia_slug": "Chimney_swift"
    },
    "Peregrine Falcon": {
        "scientific_name": "Falco peregrinus",
        "guild": "Resident Urban Apex Raptor",
        "habitat": "High-Rise Building Ledges & Bridge Trusses",
        "description": "World's fastest animal, nesting on skyscraper ledges in Downtown Kansas City and hunting urban pigeons.",
        "wikipedia_slug": "Peregrine_falcon"
    },
    "Cedar Waxwing": {
        "scientific_name": "Bombycilla cedrorum",
        "guild": "Nomadic Frugivore",
        "habitat": "Berry-Bearing Street Trees & Plazas",
        "description": "Sleek crested bird with red wing tips, flocking to fruiting hackberry, serviceberry, and crabapple street trees.",
        "wikipedia_slug": "Cedar_waxwing"
    },
    "Common Nighthawk": {
        "scientific_name": "Chordeiles minor",
        "guild": "Migratory Dusk Aerial Insectivore",
        "habitat": "Flat Gravel Rooftops & Streetlamp Corridors",
        "description": "Crepuscular insect hunter giving distinctive nasal 'peent' calls over lighted parking lots and plazas at dusk.",
        "wikipedia_slug": "Common_nighthawk"
    },
    "Black-capped Chickadee": {
        "scientific_name": "Poecile atricapillus",
        "guild": "Resident Granivore / Insectivore",
        "habitat": "Backyard Feeders, Forest Edges & Parks",
        "description": "Friendly, inquisitive small songbird active year-round in urban backyards and wooded trails.",
        "wikipedia_slug": "Black-capped_chickadee"
    }
}

import functools

# Scientific Name to Common Name Lookup Mapping
SCIENTIFIC_TO_COMMON: Dict[str, str] = {
    meta["scientific_name"].lower(): name
    for name, meta in BIRD_SPECIES_TAXONOMY.items()
}

# Add extra common North American bird binomials
ADDITIONAL_BINOMIALS = {
    "dumetella carolinensis": "Gray Catbird",
    "haemorhous mexicanus": "House Finch",
    "haemorhous purpureus": "Purple Finch",
    "junco hyemalis": "Dark-eyed Junco",
    "lanius ludovicianus": "Loggerhead Shrike",
    "larus delawarensis": "Ring-billed Gull",
    "lophodytes cucullatus": "Hooded Merganser",
    "megascops asio": "Eastern Screech-Owl",
    "melanerpes erythrocephalus": "Red-headed Woodpecker",
    "melanerpes carolinus": "Red-bellied Woodpecker",
    "dryobates pubescens": "Downy Woodpecker",
    "picoides pubescens": "Downy Woodpecker",
    "sitta carolinensis": "White-breasted Nuthatch",
    "spizella passerina": "Chipping Sparrow",
    "zenaida macroura": "Mourning Dove",
    "bucephala albeola": "Bufflehead",
    "anas platyrhynchos": "Mallard",
    "ardea herodias": "Great Blue Heron",
    "passer domesticus": "House Sparrow",
    "spinus tristis": "American Goldfinch",
    "turdus migratorius": "American Robin",
    "sturnus vulgaris": "European Starling"
}
SCIENTIFIC_TO_COMMON.update(ADDITIONAL_BINOMIALS)

@functools.lru_cache(maxsize=256)
def resolve_common_name(name_or_scientific: str) -> str:
    """
    Resolve a scientific or common bird species string to its English Common Name.
    Uses static taxonomy mapping first, then queries iNaturalist Open API dynamically.
    """
    if not name_or_scientific:
        return "Unknown Bird"
    name_clean = name_or_scientific.strip()
    if name_clean in BIRD_SPECIES_TAXONOMY:
        return name_clean
    lower_name = name_clean.lower()
    if lower_name in SCIENTIFIC_TO_COMMON:
        return SCIENTIFIC_TO_COMMON[lower_name]

    # Dynamic fallback query to iNaturalist REST API for any missing species
    try:
        url = f"https://api.inaturalist.org/v1/taxa?q={requests.utils.quote(name_clean)}"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                pref_common = results[0].get("preferred_common_name")
                if pref_common:
                    common_title = pref_common.title()
                    SCIENTIFIC_TO_COMMON[lower_name] = common_title
                    return common_title
    except Exception:
        pass

    return name_clean

@functools.lru_cache(maxsize=256)
def get_canonical_taxon(name_or_scientific: str) -> TaxonRef:
    """
    Resolve any common or scientific species string to a single canonical TaxonRef object.
    Ensures GBIF, eBird, iNaturalist, phenology, and search modes match on taxon_id.
    """
    if not name_or_scientific:
        return TaxonRef(taxon_id="unknown_bird", scientific_name="Unknown", common_name="Unknown Bird")

    common = resolve_common_name(name_or_scientific)
    curated = BIRD_SPECIES_TAXONOMY.get(common, {})
    sci_name = curated.get("scientific_name", name_or_scientific.strip())
    
    # Standardize taxon_id as lowercase underscore string
    taxon_id = sci_name.lower().strip().replace(" ", "_")
    return TaxonRef(taxon_id=taxon_id, scientific_name=sci_name, common_name=common)

def fetch_wikipedia_species_info(species_name: str, timeout: int = 4) -> Optional[Dict[str, str]]:
    """
    Fetch thumbnail image URL, species summary, and Wikipedia link from Wikipedia REST API.
    """
    common_name = resolve_common_name(species_name)
    meta = BIRD_SPECIES_TAXONOMY.get(common_name, {})
    slug = meta.get("wikipedia_slug", common_name.replace(" ", "_"))

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
    headers = {"User-Agent": "OVON-ResearchApp/1.0 (contact@ovon-project.org)"}

    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            return {
                "photo_url": data.get("thumbnail", {}).get("source", ""),
                "description": data.get("extract", meta.get("description", "")),
                "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception:
        pass

    return None

def fetch_inaturalist_species_info(species_name: str, timeout: int = 4) -> Optional[Dict[str, Any]]:
    """
    Fetch species metadata, common name, and photo from iNaturalist Open REST API.
    """
    common_name = resolve_common_name(species_name)
    url = f"https://api.inaturalist.org/v1/taxa?q={requests.utils.quote(common_name)}"

    try:
        res = requests.get(url, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                t = results[0]
                photo = t.get("default_photo", {}).get("medium_url") or t.get("default_photo", {}).get("square_url", "")
                pref_common = t.get("preferred_common_name", common_name)
                sci_name = t.get("name", "")
                return {
                    "preferred_common_name": pref_common.title(),
                    "scientific_name": sci_name,
                    "photo_url": photo,
                    "conservation_status": t.get("conservation_status", {}).get("status_name", "Least Concern (IUCN)")
                }
    except Exception:
        pass

    return None

def get_enriched_species_metadata(species_name: str) -> SpeciesMetadata:
    """
    Retrieve comprehensive species metadata combining curated taxonomy, iNaturalist API, and Wikipedia API.
    """
    common_name = resolve_common_name(species_name)
    curated = BIRD_SPECIES_TAXONOMY.get(common_name, {})

    sci_name = curated.get("scientific_name", common_name)
    guild = curated.get("guild", "Urban Avian Species")
    habitat = curated.get("habitat", "Urban Parks & Open Space")
    desc = curated.get("description", "Observation target species for Greater Kansas City pilot region.")
    photo_url = "https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=400"
    wiki_url = f"https://en.wikipedia.org/wiki/{common_name.replace(' ', '_')}"

    # Query Wikipedia REST API for photo & extract
    wiki_res = fetch_wikipedia_species_info(common_name)
    if wiki_res:
        if wiki_res.get("photo_url"):
            photo_url = wiki_res["photo_url"]
        if wiki_res.get("description"):
            desc = wiki_res["description"]
        if wiki_res.get("wikipedia_url"):
            wiki_url = wiki_res["wikipedia_url"]

    # Query iNaturalist REST API if photo still generic
    if "unsplash" in photo_url:
        inat_res = fetch_inaturalist_species_info(common_name)
        if inat_res and inat_res.get("photo_url"):
            photo_url = inat_res["photo_url"]

    return SpeciesMetadata(
        common_name=common_name,
        scientific_name=sci_name,
        guild_class=guild,
        primary_habitat=habitat,
        photo_url=photo_url,
        description=desc,
        wikipedia_url=wiki_url
    )
