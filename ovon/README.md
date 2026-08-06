# 🦅 Optimal Volunteer Observation Network (OVON)

**Working Acronym:** OVON  
**Pilot Region:** Greater Kansas City & Missouri–Kansas Border Landscape (`39.0997, -94.5786`)  
**Research Domain:** Computational Ecology, Citizen Science Design, Spatial Statistics & Combinatorial Routing Optimization  
**Current Version:** 1.0 (Milestones 1–5 Complete)  
**Last Updated:** 2026-08-05

---

## 📌 Executive Summary

OVON answers a fundamental question in citizen science and ecological monitoring:

> **Given a limited amount of volunteer time, where and when should people observe birds so their checklists create the most new scientific value?**

The best birding spot is rarely the best scientific sampling location. Highly popular birding hotspots (like famous wetlands) receive redundant checklists, yielding diminishing scientific returns. OVON designs **human-aware, route-constrained multi-species observation routes** that maximize scientific information gain under real-world time, travel, safety, and accessibility constraints.

---

## 🚀 Key Accomplishments & Features (Milestones 1–5 Complete)

- ✅ **Milestone 1: Mathematical Kernel (`src/ovon/utility/metrics.py`, `src/ovon/routing/optimizer.py`)**
  - Binary Bernoulli entropy, Query-by-Committee (QBC) model disagreement, and spatial-habitat Gaussian redundancy kernels $k(a, b)$.
  - Multi-species set utility optimizer using greedy marginal efficiency construction and 2-opt local search refinement.

- ✅ **Milestone 2: Real GIS & POI Ingestion (`src/ovon/data/fetch_public.py`)**
  - OpenStreetMap integration for Kansas City parks, famous public fountains (J.C. Nichols Memorial Fountain, Firefighters Fountain, Loose Park Rose Garden Fountain), plazas, and riverfronts.
  - GBIF open biodiversity API integration for real species occurrence records across Kansas City (*Bald Eagle*, *Indigo Bunting*, *Yellow-rumped Warbler*, *Belted Kingfisher*, *Cardinal*, etc.).

- ✅ **Milestone 3: Spatial 3 km Grid & Redundancy Atlas (`src/ovon/features/`)**
  - Equal-area 3 km spatial grid (1,156 grid cells ~9 km² each) centered on Greater Kansas City.
  - Spatiotemporal redundancy atlas ranking priority under-observed spatial cells during key seasonal windows (e.g. spring migration week 18).

- ✅ **Milestone 4: Species Encounter Models & Uncertainty Engine (`src/ovon/models/encounter.py`)**
  - Calibrated Random Forest models predicting standardized encounter probabilities $\hat{\pi}_{sit} \in [0, 1]$.
  - Spatial Block Cross-Validation (`SpatialBlockCV`) and Spatial Bootstrap Ensembles (`BootstrapEnsembleUncertainty`) generating epistemic model disagreement layers.

- ✅ **Milestone 5: OSRM Real Road & Walking Routing (`src/ovon/routing/osrm.py`)**
  - Open Source Routing Machine API integration rendering **road-snapped polylines** along highways or **pedestrian trail polylines** along urban footpaths.
  - Turn-by-turn volunteer driving directions and pedestrian walking instructions.

- ✅ **Urban Pedestrian & Transit Circuit Expansion (`src/ovon/data/fetch_urban.py`)**
  - Ingestion of urban footways, greenways (Trolley Track Trail, Brush Creek Corridor), historic cemeteries (Union Cemetery), fountains, and KC Streetcar transit hubs.
  - Walkable 1.5–5.0 km transit-anchored closed-loop itineraries (4.5 km/h walking travel matrices with 5-minute micro-stationary counts).

- ✅ **Interactive Web Research Dashboard (`src/ovon/app.py`)**
  - Streamlit + Folium map interface with form-based controls eliminating map flicker.
  - Species map filter, color-coded sighting pins, spatial grid uncertainty heatmaps, observer experience profile controls (`Beginner`, `Intermediate`, `Advanced`), and model calibration tabs.

---

## 💻 Quick Start & Running locally

Make sure you are in the `ovon` project directory (`cd ovon`):

```bash
cd ovon
```

### 1. Run Automated Test Suite (24 Passing Tests)
```bash
cmd /c "set PYTHONPATH=src && pytest -v"
```

### 2. Launch Interactive Web Dashboard
- **From inside `ovon/` directory:**
  ```bash
  py -3.12 -m streamlit run src/ovon/app.py --server.port 8501
  ```
- **From the workspace root (`the_x_files`):**
  ```bash
  cmd /c "set PYTHONPATH=ovon\src && py -3.12 -m streamlit run ovon/src/ovon/app.py --server.port 8501"
  ```
Open your browser at **[http://localhost:8501](http://localhost:8501)**.

### 3. CLI Commands
```bash
# From inside ovon/
python src/ovon/cli.py fetch-kc


# Build projected 3 km equal-area spatial grid
python src/ovon/cli.py grid-build

# Report priority under-observed spatial cells
python src/ovon/cli.py report-redundancy --week 18

# Run OVON route optimizer on real KC landscape
python src/ovon/cli.py optimize-route --real-kc --budget 90

# Evaluate species encounter models and spatial block CV metrics
python src/ovon/cli.py model-evaluate

# Run policy benchmark comparison (OVON vs Hotspot vs Random)
python src/ovon/cli.py evaluate-baseline --real-kc
```

---

## 📁 Repository Sitemap & Directory Structure

```text
c:\Users\admir\Github\the_x_files\ovon\
├── pyproject.toml              # Project dependencies & pytest configuration
├── README.md                   # Project sitemap & quick start guide
├── 01_RESEARCH_LANDSCAPE.md    # Theoretical foundations & background
├── 02_DATA_PLAN.md             # eBird, OpenStreetMap, & GBIF data plan
├── 03_MATHEMATICAL_FRAMEWORK.md# Mathematical equations, entropy, & QBC formulation
├── 04_EXPERIMENTS_AND_HYPOTHESES.md # Benchmark policies & hypotheses
├── 05_IMPLEMENTATION_ROADMAP.md # Milestone completion status matrix
├── 06_VALIDATION_RISKS_AND_ETHICS.md # Ethics, safety, & access constraints
├── 07_PROJECT_DECISIONS.md     # Architecture Decision Records (ADR-001 to ADR-019)
├── 08_REFERENCES.md            # Academic references
├── config/
│   └── project.yml             # Regional bounds & default parameters
├── src/ovon/
│   ├── app.py                  # Streamlit + Folium interactive web dashboard
│   ├── cli.py                  # Command line interface commands
│   ├── config.py               # Config dataclass loader
│   ├── synthetic/
│   │   └── generator.py        # Synthetic landscape & candidate site generator
│   ├── utility/
│   │   └── metrics.py          # Bernoulli entropy, QBC disagreement, Gaussian redundancy
│   ├── routing/
│   │   ├── optimizer.py        # Greedy 2-opt route optimizer & baselines
│   │   └── osrm.py             # OSRM road driving polylines & turn-by-turn steps
│   ├── data/
│   │   └── fetch_public.py     # OpenStreetMap parks/fountains & GBIF bird fetcher
│   ├── features/
│   │   ├── grid.py             # EqualAreaGrid (3 km projected spatial grid)
│   │   └── redundancy.py       # RedundancyAtlas (spatiotemporal density & gaps)
│   └── models/
│       └── encounter.py        # CalibratedTreeEncounterModel & SpatialBlockCV
└── tests/
    ├── test_app.py             # App syntax & import tests
    ├── test_grid.py            # Spatial grid & redundancy atlas unit tests
    ├── test_models.py          # Calibrated models & spatial block CV tests
    ├── test_osrm.py            # OSRM road routing & turn-by-turn tests
    ├── test_public_data.py     # Public GIS & GBIF data tests
    ├── test_routing.py         # Route budget & optimizer unit tests
    └── test_utility.py         # Mathematical metrics unit tests
```

---

## 📑 Resumption Guide for New Chat Sessions

When resuming work in a fresh context window:
1. All core project deliverables are in `c:\Users\admir\Github\the_x_files\ovon`.
2. Run `pytest -v` to verify the test suite (all 24 tests should pass).
3. Check [`05_IMPLEMENTATION_ROADMAP.md`](file:///c:/Users/admir/Github/the_x_files/ovon/05_IMPLEMENTATION_ROADMAP.md) and [`07_PROJECT_DECISIONS.md`](file:///c:/Users/admir/Github/the_x_files/ovon/07_PROJECT_DECISIONS.md) for current architectural decisions.
4. Launch the dashboard server using `py -3.12 -m streamlit run src/ovon/app.py --server.port 8501`.
