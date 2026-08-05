# Experiments, Hypotheses, and Evaluation Design

## 1. Research program

The project is divided into four core studies and one extension:

1. **Study A:** quantify spatial, temporal, habitat, protocol, and observer redundancy;
2. **Study B:** benchmark adaptive sampling through historical replay;
3. **Study C:** evaluate route-constrained and human-aware optimization;
4. **Study D:** run a prospective field feasibility pilot;
5. **Study E:** compare entropy reduction with decision-focused value of information.

Each study should produce an independently useful result. The analytical contribution should not depend on a successful field pilot.

## 2. Common design principles

### 2.1 Define what the system is trying to learn

Every optimization result must identify its target, such as:

- weekly encounter-rate surface for one species;
- migration timing;
- habitat response;
- a community latent factor;
- occupancy at fixed repeated-visit sites;
- a monitoring or management decision.

“Most informative” has no meaning without a target.

### 2.2 Separate training and evaluation in space and time

Random row splitting is inadequate because neighboring checklists and repeated visits are dependent. Use:

- rolling future-year holdouts;
- spatial blocks;
- site or checklist-group blocking;
- observer grouping for selected tests;
- route and participant grouping for prospective data.

### 2.3 Compare with strong simple baselines

The adaptive method must compete with practical low-cost policies:

- random feasible sampling;
- equal-area coverage;
- least-sampled cells;
- environmental stratification;
- hotspot visits;
- maximum pointwise uncertainty;
- shortest travel route.

### 2.4 Evaluate realized value

For prospective deployment:

\[
\text{realized value}=
\mathbf 1\{\text{completed}\}
\times \text{data quality}
\times \text{scientific utility}.
\]

An uncompleted theoretically optimal route contributes no data.

---

# Study A: Observation redundancy and coverage

## A1. Research question

How much eBird effort in the Kansas City region is genuinely repetitive after accounting for ecological, temporal, protocol, and observer similarity?

## A2. Hypotheses

### H-A1: Hotspot redundancy

After controlling for habitat, week, protocol, effort, and observer concentration, established hotspots will have lower average marginal information per additional checklist than comparable non-hotspot locations.

**Null:** hotspot status is unrelated to marginal information after controls.

### H-A2: Temporal concentration during migration

During migration, filling a missing week at a known location will often be more valuable than adding a nearby new location during a well-sampled week.

**Null:** temporal gaps do not gain relative value during rapid seasonal change.

### H-A3: Independent-observer diversity

Cell-weeks with many checklists but few independent observers will yield less robust inference than cell-weeks with similar checklist totals distributed across more observers.

**Null:** observer diversity adds no calibration or generalization value after checklist count and effort are controlled.

### H-A4: Habitat-aware coverage

Raw checklist density will misclassify some places as well sampled because nearby observations are concentrated in one habitat or protocol type.

**Null:** raw spatial density performs as well as habitat-aware effective coverage.

### H-A5: Redundancy is species-specific

A location can be redundant for common generalists but informative for a habitat specialist or seasonal migrant.

**Null:** one species-independent coverage score captures marginal value adequately.

## A3. Methods

1. Build weekly 3 km cell summaries.
2. Calculate:
   - checklist count;
   - independent-observer count;
   - hotspot share;
   - protocol and effort diversity;
   - habitat diversity;
   - ecological–spatiotemporal kernel coverage;
   - focal-species prevalence.
3. Fit baseline encounter models.
4. Approximate each checklist’s marginal contribution using deletion, influence, bootstrap, or sequential-addition analyses.
5. Measure change in:
   - future log loss;
   - Brier score;
   - calibration;
   - integrated bootstrap disagreement;
   - environmental coverage.
6. Compare raw density, kernel coverage, and model-derived uncertainty.

## A4. Primary outcomes

- distribution of marginal value per checklist;
- percentage of effort in the highest-redundancy decile;
- discordance between raw and habitat-aware coverage;
- seasonal balance of spatial versus temporal marginal value;
- marginal-value concentration by hotspot and observer.

## A5. Visual outputs

- redundancy atlas;
- week-by-week information-gap animation;
- checklist count versus marginal value;
- matched hotspot/non-hotspot comparisons;
- observer concentration map;
- habitat-by-week coverage matrix.

## A6. Falsification and pivot

The complex redundancy metric is weakened if checklist density predicts marginal contribution equally well, hotspot records remain equally valuable after adjustment, or temporal effects vanish under spatial blocking. A simple result is acceptable and may justify a much cheaper field strategy.

---

# Study B: Historical adaptive-sampling benchmark

## B1. Research question

Under a fixed number of additional checklists, which selection policy most improves future ecological prediction or coverage?

## B2. Counterfactual challenge

For a location that was never sampled, its historical checklist outcome is unknown. The benchmark therefore needs several complementary modes.

### Mode 1: Held-out future checklist pool

1. Split data into model history, candidate future pool, and later evaluation set.
2. Hide outcomes in the candidate pool.
3. Allow policies to use only pre-observation site, time, effort template, and covariates.
4. Select candidate events.
5. Reveal selected outcomes and update the model.
6. Evaluate on the separate later reference set.

This uses real outcomes but only at locations people actually visited.

### Mode 2: Cell-week candidate/reference split

Within sufficiently dense cell-weeks, separate actual checklists into candidate and reference pools. Policies select candidate observations, while independent reference checklists evaluate the updated model.

### Mode 3: Semi-synthetic known truth

1. Fit a high-capacity reference ecological and observation model.
2. Treat its latent field as simulation truth.
3. simulate detections under realistic effort, observer, and spatial-bias patterns;
4. compare policies with known counterfactual outcomes.

This provides controlled truth but inherits the simulator’s assumptions.

## B3. Policies

| Code | Policy |
|---|---|
| P0 | random feasible sample |
| P1 | hotspot or high historical richness |
| P2 | fewest prior checklists |
| P3 | equal-area spatial coverage |
| P4 | environmental diversity |
| P5 | pointwise predictive entropy |
| P6 | bootstrap model disagreement |
| P7 | expected integrated variance reduction |
| P8 | redundancy-aware multi-species utility |
| P9 | oracle using hidden truth; benchmark only |

## B4. Hypotheses

### H-B1: Redundancy-aware performance

P8 will improve predeclared held-out calibration or predictive loss more per selected checklist than P0–P5.

### H-B2: Pointwise entropy limitation

P5 will sometimes select clusters of similar high-entropy sites and underperform set-aware P7 or P8.

### H-B3: Least-sampled limitation

P2 will select some locations that are under-sampled but ecologically uninformative, inaccessible, out of support, or irrelevant to the focal target.

### H-B4: Species heterogeneity

No single policy will dominate for every species. Gains should be largest for moderately prevalent species with structured spatial or seasonal uncertainty.

### H-B5: Migration timing

Adaptive-policy gains will be larger during periods of rapid seasonal change than during stable resident periods.

### H-B6: Simple environmental stratification is competitive

P4 may capture a large share of the benefit at a fraction of the modeling cost.

This is intentionally included as a serious competing hypothesis.

## B5. Rolling evaluation

Example evaluation sequence:

- train through 2021; select and evaluate within 2022 using separated periods;
- train through 2022; evaluate 2023;
- train through 2023; evaluate 2024;
- train through 2024; evaluate 2025.

Selection budgets:

\[
k\in\{10,25,50,100,250\}.
\]

Repeat pool construction and uncertainty estimation with fixed random seeds and blocked bootstraps.

## B6. Metrics

### Predictive quality

- log loss;
- Brier score;
- calibration intercept and slope;
- expected calibration error;
- precision–recall AUC for lower-prevalence species;
- spatially weighted error.

### Uncertainty

- integrated bootstrap variance or disagreement;
- interval coverage;
- interval width;
- posterior or ensemble entropy.

### Coverage

- distinct cells;
- habitat strata;
- under-sampled weeks filled;
- independent observers represented;
- environmental convex-hull expansion.

### Efficiency

- improvement per checklist;
- improvement per observation minute;
- improvement per travel minute;
- runtime and memory.

## B7. Statistical comparison

Use paired comparisons within species, year, week, budget, and replay replicate. Report:

- mean and median paired differences;
- blocked bootstrap confidence intervals;
- probability of practical superiority;
- win/loss distributions;
- rank stability;
- heterogeneity by species guild and season.

Avoid relying on one aggregate p-value across millions of checklist rows.

---

# Study C: Route-constrained and human-aware optimization

## C1. Research question

How much of the theoretical benefit of adaptive site selection survives realistic travel, accessibility, observer capability, and route-completion constraints?

## C2. Route classes

- 45-minute local route;
- 90-minute standard route;
- 180-minute regional route;
- wheelchair-accessible route;
- beginner route;
- advanced survey route;
- coordinated multi-volunteer route.

Every budget includes both travel and observation time.

## C3. Hypotheses

### H-C1: Joint route optimization

Selecting the top \(k\) sites independently and routing them afterward will yield less information per minute than optimizing information and travel jointly.

### H-C2: Diminishing returns

Routes deliberately covering different habitats, weeks, or uncertainty modes will outperform routes containing nearby but highly similar stops.

### H-C3: Beginner contribution

Beginner-matched routes focused on common detectable species and standardized repeated stops will create positive scientific value and outperform assigning beginners to generic high-uncertainty routes.

### H-C4: Completion-adjusted utility

A completion-aware policy will produce higher expected realized value than a science-only policy even when its theoretical information score is lower.

### H-C5: Accessibility frontier

Requiring a substantial portfolio of accessible routes will have a measurable but potentially modest cost because many high-value locations have accessible substitutes.

This is a testable hypothesis, not an assumption.

### H-C6: Menus outperform single assignments

Offering a small menu of diverse high-value routes will increase completion with little loss in expected scientific utility compared with assigning one route.

## C4. Algorithms

- top-\(k\) plus shortest tour;
- nearest-neighbor with node rewards;
- greedy marginal utility per added minute;
- beam search;
- local search with insert/delete/swap/2-opt;
- exact or mixed-integer optimization for small benchmark cases;
- multi-route greedy assignment with overlap control.

Use exact solutions on small instances to estimate heuristic optimality gaps.

## C5. Route-level outputs

For every generated route report:

- total scientific utility;
- utility decomposition by species, habitat, and week;
- travel and observation time;
- number of stops;
- habitat diversity;
- accessibility and difficulty;
- public-access confidence;
- expected completion;
- stability across model bootstrap samples;
- a short human-readable explanation.

## C6. Explanation experiment

Candidate route messages:

1. “This location is under-observed.”
2. “This route fills a missing week during migration.”
3. “Common-species detections and non-detections are scientifically useful here.”
4. “This route covers three habitat types missing from this week’s records.”
5. no explanation.

Test explanations only in the prospective stage and review them for burden, transparency, and consent.

---

# Study D: Prospective field feasibility pilot

## D1. Goal

Test feasibility, completion, data quality, and model calibration—not definitive population impact.

## D2. Participants

A planning range of 20–40 volunteers across experience levels is reasonable for feasibility work, but it is not a confirmatory powered sample. Ask participants to attempt more than one route so within-person comparisons are possible.

## D3. Field unit

- route with 3–5 fixed public stops;
- 10–15 minute stationary complete checklist per stop;
- fixed observation location;
- appropriate time-of-day window;
- no playback;
- standard safety and access instructions;
- optional paired beginner/experienced teams.

## D4. Candidate experimental arms

A feasible pilot could compare:

1. convenience-oriented route;
2. information-optimized route;
3. information-optimized menu of three routes.

Do not divide a small sample into too many arms. A two-arm crossover may be preferable.

## D5. Feasibility outcomes

- route acceptance;
- route completion;
- stops completed;
- complete-checklist rate;
- valid effort metadata;
- participation within the target window;
- reported burden;
- safety or access failures;
- willingness to repeat;
- predicted versus actual route duration.

## D6. Scientific outcomes

- focal-species detections and non-detections;
- new habitat and week coverage;
- change in predictions;
- change in uncertainty;
- repeated-visit detection estimates;
- systematic model mismatch in under-sampled strata.

## D7. Hypotheses

### H-D1: Route-menu completion

A short menu will achieve higher completion than a single nonpersonalized route.

### H-D2: Protocol precision

Short stationary point routes will produce more spatially precise and model-usable records than ordinary long traveling outings.

### H-D3: Beginner feasibility

After a short protocol orientation, beginners can provide high-quality complete checklists for a defined common-species portfolio.

### H-D4: Model mismatch discovery

Prospective routes will reveal systematic errors in at least some under-sampled habitat or seasonal strata.

## D8. Analysis

Use participant-level or hierarchical models where appropriate. Focus on effect sizes, intervals, completion heterogeneity, failure reasons, and variance estimates for a later trial. Do not treat every stop as an independent participant.

## D9. Progression criterion

Proceed to a larger study if access failures are rare and correctable, completion is operationally sufficient, complete-checklist quality is acceptable, adaptive routes add measurable coverage or calibration value, and volunteers report manageable burden.

---

# Study E: Entropy versus conservation value

## E1. Research question

Do routes that maximally reduce prediction uncertainty also improve a concrete monitoring or conservation decision?

## E2. Candidate decision

Select a limited set of sites for a structured seasonal monitoring network. Adaptive observations have value when they change the chosen portfolio or improve its expected performance.

## E3. Compared policies

- maximum predictive entropy;
- maximum integrated variance reduction;
- maximum expected value of sample information;
- environmental stratification;
- expert-designed survey.

## E4. Hypothesis

Decision-focused sampling will outperform pure entropy reduction when budgets are small and management priorities are concentrated, while entropy may provide broader map-learning benefits.

## E5. Importance

A positive result shows that “most uncertain” and “most worth resolving” differ. A negative result supports simpler uncertainty-based planning.

---

# 7. Ablation studies

Remove one component at a time:

- effort correction;
- complete-checklist restriction;
- spatial subsampling;
- temporal modeling;
- habitat similarity;
- observer component;
- route constraint;
- completion model;
- redundancy penalty;
- multi-species utility;
- 1 km versus 3 km versus 5 km grid.

Ablations identify where gains actually originate.

## 8. Robustness analyses

- alternative focal-species portfolios;
- alternative model families;
- different spatial and temporal blocks;
- exclusion of top hotspots;
- exclusion of highest-volume observers;
- broad versus strict effort filters;
- different route budgets;
- leave-one-year-out tests;
- Missouri-only and Kansas-only analyses;
- weather-stratified analysis;
- no use of Status and Trends products.

## 9. Pre-registration table

Freeze before the final primary evaluation:

| Decision | Initial planned value |
|---|---|
| historical endpoint | 2025-12-31 |
| primary grid | 3 km equal-area |
| temporal unit | week |
| focal species | rule-based portfolio plus ecological review |
| primary outcomes | held-out log loss and calibration |
| primary adaptive policy | redundancy-aware multi-species utility |
| primary baselines | P0, P2, P3, P4, P5 |
| route budget | frozen before route comparison |
| bootstrap unit | spatial-temporal block |
| checklist rules | complete + documented effort filters |
| reporting | paired effect sizes and blocked intervals |

## 10. Potential paper packages

### Paper 1: Redundancy

*The Marginal Value of Another Checklist: Measuring Redundancy in Semi-Structured Bird Observation Networks*

### Paper 2: Algorithm and benchmark

*Human-Aware Informative Orienteering for Multi-Species Citizen Science*

### Paper 3: Field feasibility

*Can Volunteer Birders Be Nudged Toward More Informative Observation Routes? A Kansas City Pilot*

### Paper 4: Decision value

*Where Uncertainty Matters: Comparing Entropy and Conservation Value in Adaptive Biodiversity Surveys*
