# 🌆 OVON Urban Pedestrian & Micro-Habitat Expansion Strategy

This document outlines the strategic, mathematical, and data architecture framework for expanding OVON from a car-centric regional park optimizer into an **urban pedestrian-first, transit-accessible adaptive sampling platform**.

---

## 🎯 Core Philosophy Shift

| Feature | Legacy OVON (Car-Centric) | Urban Pedestrian OVON (Walk-First) |
| :--- | :--- | :--- |
| **Primary Transit Mode** | Automobile driving along highways (I-70, I-435) | Walking circuits, greenway trails, pedestrian paths & transit hubs |
| **Starting Locations** | Major suburban/county park parking lots | KC Streetcar stops, KCATA bus hubs, plaza fountains, community gardens |
| **Spatial Scale** | 30–50 km regional bounding box | 1.5–5.0 km walkable neighborhood circuits (45–90 min total walk time) |
| **Sampling Protocol** | 10-min stationary checklists per driving stop | 5-min micro-stationary counts + traveling checklists along urban footpaths |
| **Habitat Granularity** | Coarse 3-class land cover (forest, wetland, urban) | Micro-habitats: street canopy corridors, bioswales, pocket parks, rooftop edges |

---

## 🏙️ Granular Urban POI Taxonomy & Data Sources

To capture urban locations that are currently missed, we expand our GIS ingestion beyond standard `leisure=park` tags:

### 1. Granular OpenStreetMap (OSM) Tags
- **Greenways & Linear Corridors**: `highway=footway`, `highway=pedestrian`, `highway=path`, `leisure=track`, `railway=abandoned` (rails-to-trails like Trolley Track Trail).
- **Urban Micro-Green Spaces**: `leisure=garden`, `amenity=community_centre` (community gardens), `historic=cemetery` (historic wooded cemeteries like Union Cemetery).
- **Water Features & Riparian Buffers**: `amenity=fountain`, `waterway=stream`, `waterway=canal`, `natural=wetland` (urban stormwater basins, Brush Creek Corridor).
- **Public Plazas & Landmarks**: `tourism=attraction`, `place=square`, `amenity=marketplace`.

### 2. Open Data Portals & Urban Layers
- **Kansas City Open Data (KC OpenData API)**:
  - KC Parks & Recreation Trails layer (Brush Creek Trail, Trolley Track Trail, Cliff Drive Scenic Byway).
  - KC Streetcar Stop coordinates (River Market \(\leftrightarrow\) Union Station \(\leftrightarrow\) Plaza extension).
  - KCATA RideKC Bus Transit Hubs (Main Street MetroLink, Prospect MAX).
- **EPA EnviroAtlas & Tree Canopy GIS**:
  - High-resolution urban tree canopy density (percent tree cover per block group).
  - Urban heat island & impervious surface cover.

---

## 🚶‍♂️ Pedestrian Routing Engine & OSRM Walking Profile

### 1. OSRM Foot Profile API
Instead of vehicle road snapping, OVON will query the Open Source Routing Machine **walking profile**:
```http
https://router.project-osrm.org/route/v1/walking/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&steps=true
```
This routes along actual sidewalks, park trails, footbridges, and crosswalks while ignoring one-way road restrictions.

### 2. Transit-Anchored Closed-Loop Itineraries
Routes will default to **Transit-Anchored Walking Circuits**:
1. **Start**: Public Transit Hub (e.g. KC Streetcar Union Station Stop).
2. **Walk Leg 1**: 10-min walk along street canopy corridor \(\rightarrow\) **Stop 1**: Penn Valley Park Pond (5-min count).
3. **Walk Leg 2**: 8-min walk along Brush Creek Greenway \(\rightarrow\) **Stop 2**: Firefighters Fountain (5-min count).
4. **Walk Leg 3**: 12-min walk through historic neighborhood \(\rightarrow\) **Return**: Main St Streetcar / Bus Stop.

---

## 🦅 Urban Focal Species & Micro-Habitat Analytics

Urban environments feature distinct species assemblages adapted to built structures and urban greening:

| Species | Primary Urban Micro-Habitat | Detectability & Protocol Guidance |
| :--- | :--- | :--- |
| **Chimney Swift** | Masonry chimneys, downtown brick buildings | Dusk flyover counts near roost chimneys; high audio detectability |
| **Peregrine Falcon** | High-rise building ledges, bridge trusses | Overhead scanning on downtown plaza stops |
| **Cedar Waxwing** | Berry-bearing street trees (*Celtis*, *Crataegus*) | Tree canopy scanning in pocket parks and plazas |
| **Common Nighthawk** | Flat gravel rooftops, streetlamp corridors | Evening dusk walking transects |
| **Warblers (Spring/Fall)** | Urban park tree groves, cemetery mature oaks | High-frequency morning vocalization counts in urban oases |
| **Black-capped Chickadee** | Neighborhood backyard buffers, bird feeders | High detectability across all urban experience levels |

---

## 🏗️ Proposed Implementation Architecture

### Phase 1: Ingestion & Routing Engine
1. **`src/ovon/data/fetch_urban.py`**:
   - Overpass query fetching footways, community gardens, streetcar stops, and fountains across Downtown, Midtown, Plaza, and Westport.
2. **`src/ovon/routing/osrm.py`**:
   - Add `profile="walking"` parameter to `fetch_osrm_route` and `fetch_osrm_multistop_route`.

### Phase 2: Optimizer & UI Modes
1. **`src/ovon/routing/optimizer.py`**:
   - Add `travel_mode: str = "walking"` (walking speed: 4.5 km/h vs driving speed: 30–40 km/h).
2. **`src/ovon/app.py`**:
   - Add **"Transit & Walking Circuit"** mode toggle.
   - Display Transit Connection Badges (e.g., "🚆 2 min walk from KC Streetcar").
