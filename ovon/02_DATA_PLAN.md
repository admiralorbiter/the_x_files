# Data Acquisition, Engineering, and Governance Plan

## 1. Data strategy

The central analysis requires **complete checklists plus sampling-event metadata**. Presence-only bird records are insufficient because they do not reveal where a volunteer searched and failed to detect a focal species.

The project should use the eBird Basic Dataset (EBD) and Sampling Event Data (SED), not only the public API or GBIF occurrence export.

## 2. Primary eBird products

### 2.1 eBird Basic Dataset

The EBD contains observation-level records. A typical row describes one taxon reported on one checklist and includes taxonomic identifiers, observation count, date, time, location, protocol, effort, observer and group identifiers, and review information.

The EBD is updated monthly. Access requires a logged-in data request. For reproducibility, record:

- exact release identifier;
- request purpose;
- approval and download dates;
- geographic and temporal filters;
- whether all species and SED were requested;
- file hash;
- recommended citation distributed with the download.

Official access information:

- [Download eBird Data Products](https://science.ebird.org/en/use-ebird-data/download-ebird-data-products)
- [Download eBird Data help](https://support.ebird.org/en/support/solutions/articles/48000838205-download-ebird-data)

### 2.2 Sampling Event Data

SED contains checklist-level metadata. Relevant fields include:

| Field | Role |
|---|---|
| sampling event identifier | event key joining observations to checklists |
| group identifier | identify shared checklists |
| observer identifier | observer-effect and repeated-participation analysis |
| observation date | temporal bin |
| start time | detectability and route compliance |
| latitude and longitude | spatial assignment |
| locality ID and type | site/hotspot context |
| protocol type | stationary, traveling, incidental, specialized |
| duration minutes | effort |
| effort distance | effort and spatial support |
| number of observers | detection effort |
| all species reported | complete-checklist filter |
| project code | specialized-protocol filtering |

The EBD and SED join on the sampling-event identifier. Shared checklists should be collapsed to one independent event before analysis.

### 2.3 Public eBird API

The API is useful for current observations, region and hotspot metadata, and application prototypes. It is not a substitute for the historical EBD/SED research extract because it offers limited recent or summarized data and does not provide the complete historical observation process required for the main analysis.

### 2.4 eBird Observational Dataset through GBIF

The EOD provides basic species, date, and location records but omits important sampling-event effort metadata. It can support preliminary mapping or pipeline prototyping, but not the primary detection/non-detection or effort-standardized models.

### 2.5 Status and Trends products

Status and Trends products contain modeled range, weekly relative abundance, and trend outputs. Potential uses include:

- external comparison;
- ecological plausibility checks;
- focal-species screening;
- semi-synthetic simulation truth.

They should not silently become app training data or web-map layers. Current terms restrict redistribution and web-based decision-support use without prior written permission from Cornell.

Sources:

- [Status and Trends data](https://science.ebird.org/en/status-and-trends/download-data)
- [Status and Trends terms](https://science.ebird.org/en/status-and-trends/products-access-terms-of-use)

## 3. Data-use constraints

The current eBird data-use summary states that raw downloaded data are available for noncommercial research and education, but are purpose-restricted, should not be passed to another user, should not be redistributed in original form, must be cited, and have requirements concerning derived products and commercial use.

Source:

- [eBird data privacy and data use](https://support.ebird.org/en/support/solutions/articles/48001078113)

### Operational consequences

1. Do not commit EBD or SED rows to a public repository.
2. Do not distribute raw extracts in a project archive.
3. Publish acquisition scripts, schemas, hashes, and aggregate results—not the raw observations.
4. Keep observer identifiers private and pseudonymized.
5. Submit a new request if the research purpose materially changes.
6. Recheck terms before launching a website or distributing route-level derived products.
7. Mask or exclude sensitive species and locations.
8. Maintain a collaborator-access log for raw data.

## 4. Pilot geography

### 4.1 Primary boundary

Use a provisional 100 km geodesic radius centered on central Kansas City. The region offers:

- urban and suburban gradients;
- both Missouri and Kansas;
- river corridors;
- grassland, woodland, agricultural, wetland, and developed habitat;
- realistic variation in volunteer travel burden.

Store the exact center and boundary in configuration rather than hard-coding them.

### 4.2 Sensitivity boundaries

Run selected analyses at:

- 50 km: highly practical local volunteer network;
- 100 km: primary pilot;
- 200 km: broader ecological and migration context;
- state-level Missouri and Kansas extracts: boundary checks.

### 4.3 Edge handling

Fit ecological models on a buffered region larger than the recommendation boundary. Report routes only within the approved pilot area.

## 5. Time scope

### Primary historical period

Use complete calendar years:

- 2021-01-01 through 2025-12-31.

Advantages:

- avoids partial-year bias;
- reflects recent participation and land cover;
- provides several migration cycles;
- limits processing compared with the full archive;
- enables rolling-year historical replay.

### Optional extension

Extend to 2011–2025 for observer-learning, rare-habitat, and long-run sensitivity analyses. Do not combine early and recent years without modeling changes in participation and technology.

### Temporal units

Use:

- ISO week for the primary model;
- cyclic day of year as a feature;
- migration-phase windows for targeted experiments;
- year as a grouping and holdout variable.

## 6. Environmental and route covariates

### 6.1 Annual NLCD

Use the USGS Annual National Land Cover Database for habitat composition and landscape structure.

Candidate features within several buffers:

- developed intensity;
- deciduous, evergreen, and mixed forest;
- shrub and grassland;
- cultivated crops and pasture;
- woody and emergent wetlands;
- open water;
- impervious surface;
- habitat diversity;
- edge density;
- recent land-cover change.

Source:

- [Annual NLCD data access](https://www.usgs.gov/centers/eros/science/annual-nlcd-data-access)

### 6.2 Daymet

Use Daymet for daily weather and seasonal conditions:

- minimum and maximum temperature;
- precipitation;
- vapor pressure;
- shortwave radiation;
- snow water equivalent;
- day length.

Source:

- [Daymet](https://daymet.ornl.gov/)

### 6.3 PAD-US

Use the Protected Areas Database of the United States as a first-stage source for:

- public-access screening;
- protected-area identity;
- managing agency;
- access category;
- conservation status.

Source:

- [PAD-US data](https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download)

PAD-US is not a perfect trail or site-access authority. Verify current hours, closures, permissions, and parking before field deployment.

### 6.4 OpenStreetMap

Use OpenStreetMap-derived networks for:

- road travel times;
- walking paths;
- parking and access points;
- route connectivity;
- surface and accessibility attributes where present.

OpenStreetMap data are licensed under ODbL and require attribution and appropriate treatment of derived databases.

Source:

- [OpenStreetMap copyright and license](https://www.openstreetmap.org/copyright)

### 6.5 Optional covariates

- elevation and terrain;
- distance to water and hydrology;
- road density;
- artificial light at night;
- census population density and vehicle access;
- park amenities;
- local flood and closure information.

Every feature should correspond to ecology, detectability, route feasibility, or equity—not merely be included because it is available.

## 7. Recommended analytical tables

### `checklist`

One row per independent checklist.

```text
checklist_id
observer_key
date
iso_week
year
start_time
latitude
longitude
protocol
duration_minutes
distance_km
number_observers
complete
hotspot_flag
group_collapsed
spatial_cell_id
```

### `detection`

One row per checklist–species pair after zero filling for focal species.

```text
checklist_id
species_id
detected
count
count_missing_flag
reviewed_flag
```

### `cell_week`

One row per spatial cell and week.

```text
cell_id
year
week
n_complete_checklists
n_independent_observers
habitat_features
weather_features
access_features
model_predictions
uncertainty_features
```

### `candidate_site`

One row per deployable sampling point.

```text
site_id
cell_id
private_latitude
private_longitude
public_display_cell
land_manager
public_access_status
parking_flag
trail_flag
wheelchair_access
safety_review_status
sensitive_location_flag
```

### `route`

One row per route, with a child stop table.

```text
route_id
start_node
end_node
travel_minutes
observation_minutes
total_minutes
expected_information
expected_completion
difficulty_class
accessibility_class
```

### `recommendation_log`

Essential once recommendations are shown to people.

```text
recommendation_id
generated_at
model_version
utility_version
candidate_set_hash
observer_profile_class
routes_offered
route_selected
route_completed
failure_reason
```

Without this table, later ecological trend analysis cannot account for the system’s influence on the sampling process.

## 8. Preprocessing rules

### 8.1 Required filters

- complete checklists for primary detection/non-detection analysis;
- stationary and traveling protocols for baseline;
- collapse shared checklists;
- roll records to the species level;
- remove records outside time and geography;
- remove impossible or missing core effort values;
- retain records consistent with the downloaded review and validation conventions.

### 8.2 Baseline effort filters

Cornell’s example uses broad weekly and approximately 3 km constraints such as stationary/traveling protocols, duration no more than six hours, distance no more than 10 km, plausible speed, and no more than 10 observers.

Use that broad set for comparability, then define a stricter sensitivity set, potentially:

- duration: 5–180 minutes;
- distance: 0–5 km;
- observers: 1–5;
- stationary or plausible walking-speed traveling surveys.

Freeze final thresholds before evaluating the primary outcome.

### 8.3 Zero filling

For every complete checklist and focal species:

- detection = 1 when the species is reported;
- detection = 0 when it is absent from the complete checklist;
- do not infer zero from incomplete checklists.

### 8.4 Shared checklists

Collapse shared checklists to one event. Preserve group size as an effort feature if appropriate, but do not count the same outing repeatedly.

### 8.5 Taxonomy

Use the taxonomy associated with the EBD release. Store stable taxon identifiers and human-readable names. Explicitly reconcile taxonomic splits and lumps across releases.

### 8.6 Coordinate precision

- keep exact coordinates in restricted storage;
- publish derived outputs at a safe aggregate scale;
- buffer habitat variables around checklist locations;
- use stricter distance filters for finer predictions.

## 9. Spatial representation

### Primary grid

Use an equal-area 3 km grid. H3 may be convenient for routing and visualization, but an equal-area projected grid makes cell-area interpretation straightforward. Choose one and document projection and neighborhood definitions.

### Multiscale covariates

Calculate habitat features at approximately:

- 500 m: local observation surroundings;
- 1.5 km: intermediate landscape;
- 3–5 km: broader context.

### Fixed field sites

For prospective occupancy or repeatability, use fixed public points rather than arbitrary cell centroids. Every site should have a repeatable location, clear access instructions, standard protocol, and safety review.

## 10. Focal-species selection

Do not select species only for charisma or rarity.

### Candidate inclusion criteria

- enough complete-checklist detections;
- sufficient spatial and temporal coverage;
- seasonal relevance;
- representation of several habitat guilds;
- varied detectability and observer difficulty;
- no sensitive-location conflict;
- interpretable ecological rationale.

### Recommended portfolio

- 4 common, relatively detectable resident species;
- 4 migratory species with strong seasonal patterns;
- 2–4 habitat specialists;
- optionally 2 lower-prevalence species for stress testing.

### Exclude from MVP

- extremely rare species;
- records dominated by chase behavior;
- taxa with unresolved identification issues;
- sensitive species whose recommendations could increase disturbance;
- species with too few spatially independent detections.

### Screening variables

```text
total detections
complete-checklist prevalence
number of occupied grid cells
weeks with adequate data
spatial concentration
hotspot concentration
observer concentration
class imbalance
seasonality strength
holdout calibration feasibility
```

An ornithologist should review the final list.

## 11. Prospective field protocol

The recommended field unit is a **short stationary complete checklist** rather than one long traveling checklist.

### Route structure

- 3–5 stops;
- 10–15 minutes per stop;
- one complete checklist per stop;
- fixed observation location;
- start time recorded;
- all detected and identified species reported;
- counts when feasible;
- no playback or disturbance;
- completion within a defined time window.

Advantages include better spatial precision, repeatability, simpler beginner instructions, and a path toward occupancy modeling.

### Repeat visits

Revisit selected sites within a biologically defensible closure period. The number and spacing of repeats should be determined with an ecologist after examining target-species detection and logistics.

## 12. Automated data card

Every data build should report:

- release and request metadata;
- row counts before and after each filter;
- complete/incomplete proportions;
- protocol distribution;
- duration and distance distributions;
- missingness;
- density by cell and week;
- shared-checklist duplicates removed;
- species prevalence;
- observer concentration;
- geographic and temporal coverage;
- sensitive-data handling;
- known license and redistribution limits.

## 13. Data freeze and reproducibility

Store:

```yaml
ebird_release:
request_purpose:
download_date:
historical_end_date:
geographic_request:
taxonomy_version:
raw_file_sha256:
preprocessing_commit:
covariate_versions:
random_seeds:
```

The raw files remain private; hashes and transformation code can be public.

## 14. Suggested data-request language

> Noncommercial research on adaptive citizen-science sampling in the Missouri–Kansas region. The project will use complete eBird checklists and Sampling Event Data to quantify spatial and temporal redundancy, estimate effort-standardized species encounter rates, and evaluate route-constrained recommendations for volunteer observations. Raw eBird data will not be redistributed. Derived outputs will be aggregated, sensitive locations will be protected, and eBird terms and citation requirements will be followed.

Retain the exact wording submitted.
