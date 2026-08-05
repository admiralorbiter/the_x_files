# Implementation Roadmap

## 1. Engineering principles

1. Build a reproducible research pipeline before an application.
2. Keep raw eBird records outside version control.
3. Make every recommendation reproducible from a model version, utility version, and candidate-set hash.
4. Implement simple baselines before advanced models.
5. Preserve a low-compute configuration throughout the project.
6. Treat public access, safety, and sensitive-species restrictions as hard constraints.
7. Log the recommendation policy once volunteers receive outputs.
8. Separate ecological modeling, information scoring, routing, and human behavior modules.

## 2. Recommended technical stack

### Extraction and preprocessing

- R with `auk` for EBD/SED parsing, shared-checklist collapse, taxonomic rollup, and zero filling;
- DuckDB plus Parquet for local analytical storage;
- Polars or data.table for fast transformations.

### Spatial processing

- `sf`/`terra` in R or GeoPandas/raster tooling in Python;
- H3 or a projected equal-area grid;
- PostGIS only if a multi-user application requires it;
- OSRM, Valhalla, or an offline routing engine for travel matrices;
- OpenStreetMap network data with attribution.

### Modeling

- GAM or logistic mixed model for interpretability;
- calibrated random forest or gradient boosting as a flexible baseline;
- spatial-temporal bootstrap ensembles for uncertainty;
- optional Stan, NIMBLE, PyMC, or occupancy-specific tools for structured field data.

### Optimization

- Python prototype using NetworkX and OR-Tools;
- exact/mixed-integer benchmark on small cases;
- optional Rust module for large candidate scoring and route local search;
- lazy marginal-gain evaluation and cached route matrices.

### Visualization and application

- reproducible static research figures first;
- internal Flask/FastAPI + HTMX or notebook dashboard second;
- public map only after terms and sensitive-location review.

## 3. Repository structure

```text
ovon/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── renv.lock
├── config/
│   ├── project.yml
│   ├── species.yml
│   ├── data_sources.yml
│   └── field_protocol.yml
├── data/
│   ├── README.md
│   ├── private/              # gitignored
│   ├── interim/              # gitignored or reproducible
│   ├── derived/
│   └── public/
├── docs/
├── R/
│   ├── extract_ebd.R
│   ├── zero_fill.R
│   ├── covariates.R
│   └── model_baselines.R
├── src/ovon/
│   ├── data/
│   ├── features/
│   ├── models/
│   ├── uncertainty/
│   ├── utility/
│   ├── routing/
│   ├── evaluation/
│   └── reporting/
├── rust/
│   └── route_search/
├── notebooks/
│   ├── 01_data_audit.qmd
│   ├── 02_redundancy.qmd
│   ├── 03_modeling.qmd
│   └── 04_replay.qmd
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/
│   └── fixtures/
├── scripts/
│   ├── build_grid.py
│   ├── fit_models.py
│   ├── score_candidates.py
│   ├── generate_routes.py
│   └── historical_replay.py
└── outputs/
    ├── figures/
    ├── tables/
    ├── model_cards/
    └── reports/
```

## 4. Configuration-first design

Example:

```yaml
project:
  name: ovon
  historical_start: 2021-01-01
  historical_end: 2025-12-31
  center:
    latitude: null
    longitude: null
  radius_km: 100

grid:
  type: equal_area_square
  resolution_km: 3
  habitat_buffers_m: [500, 1500, 3000]

checklists:
  complete_only: true
  protocols: [Stationary, Traveling]
  duration_minutes: [5, 360]
  max_distance_km: 10
  max_observers: 10

field_protocol:
  stops_per_route: [3, 5]
  minutes_per_stop: 10
  route_budget_minutes: [45, 90, 180]

model:
  target: encounter_rate
  temporal_unit: week
  bootstrap_models: 30
```

Values remain provisional until frozen in the decision log.

---

# Milestone 0: Research and governance

## Tasks

- submit EBD request;
- record exact purpose and terms;
- identify ecological reviewer;
- create sensitive-species policy;
- define public/private artifact boundaries;
- reproduce a small Cornell best-practices example.

## Acceptance criteria

- request submitted and archived;
- data README documents non-redistribution;
- one focal-species example runs end to end;
- current terms are reviewed;
- initial species-screening script exists.

---

# Milestone 1: Synthetic mathematical kernel

Build utility and routing code before depending on real data.

## Tasks

- generate synthetic cells, habitat, species probabilities, observers, and checklists;
- implement entropy, model disagreement, kernel redundancy, and GP information;
- implement cardinality-constrained greedy selection;
- implement route feasibility;
- implement greedy route and local search;
- solve small exact cases.

## Tests

- Bernoulli entropy is zero at 0 and 1 and maximal near 0.5;
- duplicate candidates have reduced marginal value;
- set utility is permutation invariant;
- every route respects the budget;
- excluded sites are never selected;
- local search never lowers the objective unless explicitly using annealing;
- exact small cases bound heuristic quality.

## Deliverable

A mathematical-kernel report with correctness tests and runtime scaling.

---

# Milestone 2: Regional data lake

## Tasks

- extract Missouri/Kansas EBD and SED;
- clip to pilot plus ecological buffer;
- collapse shared checklists;
- roll taxonomy to species;
- apply complete-checklist and effort filters;
- zero-fill focal candidates;
- write partitioned Parquet tables;
- generate data card.

## Acceptance criteria

- every detection row has a valid independent checklist key;
- no incomplete checklist contributes an inferred zero;
- row-count reconciliation is documented;
- all filters have before/after counts;
- raw data remain gitignored;
- release hash and citation are stored.

---

# Milestone 3: Coverage and redundancy atlas

## Tasks

- create cell-week aggregates;
- calculate checklist and independent-observer density;
- calculate habitat-aware effective coverage;
- measure hotspot and observer concentration;
- map seasonal gaps;
- run matched hotspot/non-hotspot comparisons.

## Acceptance criteria

- maps regenerate from one command;
- metrics are stable under reasonable kernel-bandwidth changes;
- raw versus habitat-aware differences are documented;
- sensitive outputs are masked or aggregated.

## Decision gate

Continue to expensive model-based sampling only if the redundancy analysis reveals meaningful structure beyond raw checklist density.

---

# Milestone 4: Encounter-rate baseline models

## Tasks

- choose focal species using a frozen rule;
- extract habitat, weather, effort, and temporal features;
- create spatial and temporal blocks;
- fit GAM and flexible tree baseline;
- calibrate probabilities;
- produce standardized-effort predictions;
- build bootstrap uncertainty layers.

## Acceptance criteria

For each retained species:

- prediction beats a prevalence-only baseline;
- calibration is reported on spatial and future-time holdouts;
- model failures are documented;
- uncertainty is not simply sample count;
- feature leakage checks pass.

Remove species that fail minimum quality rather than hiding the failures.

---

# Milestone 5: Offline adaptive-sampling benchmark

## Tasks

- create historical-replay pools;
- implement policies P0–P8;
- compare selection budgets;
- evaluate prediction, uncertainty, and coverage;
- run semi-synthetic truth experiments;
- run ablations and sensitivity analyses.

## Acceptance criteria

- policies use identical information available at decision time;
- outcomes remain hidden until selection;
- evaluation data are separate from selected observations;
- results include per-species and per-year distributions;
- runtime and memory are reported;
- negative results are retained.

## Decision gate

If simple environmental stratification performs as well as model-based policies, pivot toward explaining that result and building the simpler field system.

---

# Milestone 6: Public candidate-site network

## Tasks

- combine PAD-US, OSM, local park data, and verified public locations;
- define fixed candidate observation points;
- assign access confidence;
- exclude restricted and sensitive areas;
- create route-time matrix;
- classify accessibility and difficulty.

## Acceptance criteria

- every field candidate has a reviewable access source;
- private land is excluded unless permission exists;
- route-origin assumptions are documented;
- precise sensitive locations are absent from public products.

---

# Milestone 7: Route optimizer

## Tasks

- implement top-\(k\)-then-route baseline;
- implement greedy marginal utility per minute;
- implement insertion, swap, deletion, and 2-opt;
- implement route menus;
- add multi-volunteer overlap control;
- compare with exact solutions on small cases.

## Acceptance criteria

- every route meets its budget;
- utility is recomputed after every move;
- exact-benchmark gaps are measured;
- stability across uncertainty draws is reported;
- route cards include explanations.

---

# Milestone 8: Observer and completion layer

## Tasks

- define beginner/intermediate/advanced prospective profiles;
- characterize focal-species detection difficulty;
- build transparent suitability rules;
- define completion-data schema;
- simulate acceptance effects;
- prevent public individual ranking.

## Acceptance criteria

- beginner routes have explicit scientific targets;
- no participant is assigned burden solely because the model predicts compliance;
- profile use is documented and consented;
- information and burden are reported separately.

---

# Milestone 9: Internal dry run

## Tasks

- manually review generated routes;
- conduct team test outings;
- verify parking, access, timing, and safety;
- test eBird checklist instructions;
- compare predicted and actual duration;
- update site confidence.

## Acceptance criteria

- no unresolved high-risk access failures;
- instructions are understandable;
- routes can be completed through ordinary eBird submission;
- observation points and stop order are repeatable.

---

# Milestone 10: Field feasibility pilot

## Tasks

- finalize protocol and consent;
- recruit participants;
- randomize or assign route conditions;
- record offered, chosen, completed, and failed routes;
- collect burden and usability feedback;
- ingest submitted checklists;
- estimate feasibility and calibration outcomes.

## Acceptance criteria

- recommendation logs reconcile with field submissions;
- route failures have categorized reasons;
- no safety or sensitive-species incident;
- participant data are protected;
- feasibility report includes a progression recommendation.

---

# Milestone 11: Research synthesis and public release

## Tasks

- write manuscripts or preprints;
- publish code and synthetic fixtures;
- publish permitted aggregate outputs;
- satisfy derived-product and citation obligations;
- create a masked or synthetic public demonstration;
- publish model, data, and ethics cards.

## Acceptance criteria

- raw eBird data are absent from release;
- terms and attribution are reviewed;
- public products cannot reveal sensitive locations;
- all primary figures are reproducible.

## 5. Suggested 16-week analytical phase

| Week | Work |
|---|---|
| 1 | governance, data request, synthetic schema |
| 2 | reproduce eBird best-practices workflow |
| 3 | synthetic information utility |
| 4 | synthetic route optimization |
| 5 | EBD/SED extraction and quality control |
| 6 | spatial grid and environmental covariates |
| 7 | redundancy atlas |
| 8 | species screening and frozen portfolio |
| 9 | baseline encounter models |
| 10 | calibration and bootstrap uncertainty |
| 11 | historical-replay infrastructure |
| 12 | simple policy comparisons |
| 13 | redundancy-aware policy |
| 14 | route-aware benchmark |
| 15 | robustness and ablations |
| 16 | research memo and field-pilot go/no-go decision |

A field pilot begins only after ecological, access, safety, and ethics review.

## 6. Command-line interface concept

```bash
ovon data audit --config config/project.yml
ovon data build-checklists --release rel-YYYY-MM
ovon features build-grid
ovon species screen
ovon model fit --species portfolio
ovon model calibrate
ovon candidates score --week 18
ovon routes generate --budget 90 --profile beginner
ovon evaluate replay --train-end 2024-12-31 --test-year 2025
ovon report redundancy
```

## 7. Testing strategy

### Unit tests

- entropy and utility functions;
- kernels;
- date/week transformations;
- route costs;
- filtering rules;
- zero filling;
- public-access constraints.

### Property tests

- duplicate site has zero or reduced marginal value;
- increasing route budget never lowers the feasible optimum;
- input order does not change set utility;
- no route contains excluded sites;
- shared-checklist collapse is idempotent.

### Integration tests

- tiny EBD/SED fixture to final model table;
- model prediction to candidate score;
- candidate score to route;
- route to explanation;
- recommendation-log round trip.

### Statistical simulation tests

- recover a known encounter surface;
- evaluate calibration under blocked holdout;
- measure uncertainty coverage;
- compare policies under known synthetic truth.

### Regression tests

Freeze small synthetic outputs and aggregate metrics with numerical tolerances. Do not freeze unstable exact floating-point outputs from nondeterministic parallel models.

## 8. Compute profiles

### Profile A: development

- 3 species;
- 1 year;
- 10 bootstrap models;
- 100 candidate sites;
- Euclidean travel approximation.

### Profile B: MVP research

- approximately 12 species;
- 5 years;
- 30–50 bootstrap models;
- 500–2,000 candidate sites;
- road-network travel matrix;
- parallel CPU fitting.

### Profile C: extended

- 30–50 species;
- 10–15 years;
- 100+ uncertainty draws;
- dynamic occupancy;
- multiple volunteer teams.

Every major script should support Profile A for fast iteration.

## 9. Product concepts

### Research dashboard

- redundancy map;
- week slider;
- habitat coverage;
- species uncertainty;
- policy comparison;
- route utility decomposition.

### Volunteer route card

```text
Route: River and woodland morning loop
Time: 82 minutes
Stops: 4
Difficulty: Easy
Access: Public parks
Why useful:
- fills a poorly sampled migration week
- adds woodland and river-edge coverage
- common-species non-detections are useful
Protocol:
- 10 minutes stationary at each stop
- submit a complete checklist
```

Avoid opaque importance scores without explanations and uncertainty.

## 10. MVP definition of done

The MVP is complete when:

1. a reproducible historical dataset is prepared under valid terms;
2. at least eight species have calibrated encounter models;
3. redundancy and uncertainty maps are generated;
4. at least five policies are compared in historical replay;
5. route-aware recommendations are generated under realistic budgets;
6. small exact instances validate heuristic quality;
7. model, data, and ethics documentation are complete;
8. no raw or sensitive data are exposed;
9. a field-pilot go/no-go recommendation is supported by evidence.
