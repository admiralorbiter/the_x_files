# Validation, Risks, Ethics, and Responsible Deployment

## 1. Core principle

OVON influences both ecological data and human behavior. It must be evaluated as:

1. an ecological model;
2. an uncertainty estimator;
3. an optimization algorithm;
4. a volunteer-facing intervention;
5. a data-governance process.

Predictive performance alone is insufficient.

## 2. Threats to ecological validity

### 2.1 Non-detection interpreted as absence

**Risk:** A bird may be present but missed.

**Mitigation:**

- use detection/non-detection language;
- model protocol, duration, distance, time, group size, and observer effects;
- use occupancy only with repeated visits and a defensible closure period;
- label retrospective outputs as standardized encounter rate.

### 2.2 Sampling-location bias

**Risk:** Models learn where people bird rather than where birds occur.

**Mitigation:**

- complete checklists;
- spatial-temporal subsampling;
- habitat and effort variables;
- spatial and future-year validation;
- hotspot and observer sensitivity analyses;
- prospective sampling outside ordinary hotspots.

### 2.3 Adaptive feedback loop

**Risk:** Once OVON recommends locations, the observation process changes. Future models may mistake algorithm-directed effort for ecological change.

**Mitigation:**

- log every recommendation and route menu;
- record choices and completions;
- retain policy version and candidate-set hash;
- maintain some fixed reference sites;
- occasionally include randomized calibration sampling;
- use policy-aware or propensity-based correction in later trend analysis.

### 2.4 Uncertainty miscalibration

**Risk:** Bootstrap disagreement may be mistaken for total uncertainty. A misspecified model can be confidently wrong.

**Mitigation:**

- evaluate calibration on spatial and temporal holdouts;
- compare uncertainty estimators;
- flag extrapolation and out-of-distribution candidates;
- test against semi-synthetic known truth;
- state exactly which uncertainty is estimated;
- field-review high-priority areas.

### 2.5 Habitat-support mismatch

**Risk:** Checklist coordinates and habitat rasters refer to different spatial support.

**Mitigation:**

- buffer habitat features;
- use distance-based checklist filters;
- favor stationary prospective checklists;
- run multiscale analyses;
- avoid fine-resolution claims from long traveling checklists.

### 2.6 Occupancy closure violation

**Risk:** Presence changes during a repeated-visit window, especially during migration.

**Mitigation:**

- prefer encounter models during rapid movement;
- choose short, species-relevant closure periods;
- use dynamic occupancy when justified;
- consult an ornithologist before defining field windows.

## 3. Threats to causal interpretation

### 3.1 Historical replay selection bias

Only historically visited locations have real checklist outcomes.

**Mitigation:**

- distinguish held-out-event replay from true counterfactual evaluation;
- use separate candidate and reference pools;
- supplement real replay with semi-synthetic simulations;
- ultimately test recommendations prospectively.

### 3.2 Route-completion confounding

People accepting difficult routes may differ from those declining them.

**Mitigation:**

- randomize route offers where feasible;
- use crossover designs;
- record all options offered;
- report intent-to-treat and completed-route analyses;
- do not infer causal effects from completed routes alone.

### 3.3 Observer-skill confounding

Experienced observers select different places, times, and protocols.

**Mitigation:**

- model observer effects privately;
- use within-observer comparisons;
- stratify prospective assignment;
- avoid equating species count with expertise.

## 4. Sensitive species and ecological harm

### Risks

- revealing nests, roosts, or rare-species locations;
- increasing disturbance;
- encouraging off-trail access;
- creating crowding at fragile sites;
- directing people toward restricted or dangerous areas;
- indirectly exposing sensitive habitat through uncertainty maps.

### Safeguards

1. Exclude sensitive species from route-level optimization unless specifically approved.
2. Aggregate public maps.
3. Do not optimize routes around rare-bird chase reports.
4. Apply seasonal closures.
5. Prohibit playback and disturbance.
6. Prefer established public observation points.
7. Include habitat-respect instructions.
8. Allow land managers to opt out.
9. Review public outputs with a local ecological expert.
10. Keep a private sensitive-location layer separate from the public candidate network.

## 5. Volunteer dignity and fairness

### 5.1 Participants are knowledge partners

Explain:

- the scientific question;
- why non-detections can be useful;
- what data are collected;
- expected duration and difficulty;
- how results will be shared.

Do not frame participants as free interchangeable sensors.

### 5.2 No public skill ranking

Observer-effect models may improve inference but can be harmful as leaderboards.

Use:

- broad private profiles;
- self-selected difficulty;
- paired routes;
- supportive training;
- no public low-skill labels.

### 5.3 Accessibility

The route portfolio should include:

- short routes;
- stationary sites;
- wheelchair-accessible options;
- family-friendly options;
- several times of day;
- transit-compatible routes where possible;
- no-cost participation options.

### 5.4 Geographic equity

An ecological optimizer may direct all effort to remote areas while urban communities lose participation opportunities, or it may concentrate outreach among already highly engaged groups.

Report separately:

- ecological information;
- participant burden;
- geographic distribution;
- accessible-route availability;
- completion.

Do not hide tradeoffs inside one unreviewable score.

## 6. Safety

### Hard exclusions

- private property without permission;
- unsafe road shoulders;
- current flood or closure zones;
- routes conflicting with active hunting or site restrictions;
- severe weather;
- unreviewed night routes;
- uncertain access;
- illegal or off-trail movement.

### Operational controls

- verify access near deployment time;
- check weather and closures;
- include daylight buffer;
- provide route-abandonment instructions;
- use check-in/check-out for organized field studies;
- never pressure participants to complete an unsafe stop.

A model cannot certify field safety.

## 7. Privacy

### Historical observer identifiers

Pseudonymous observer IDs may become identifying when combined with place and time.

Controls:

- restricted tables;
- hashed or remapped analysis keys;
- no public individual route history;
- aggregate observer-effect results;
- access controls and retention periods.

### Prospective participants

Collect only what is necessary:

- consent;
- broad experience category;
- accessibility preferences;
- route offers, choice, and completion;
- optional feedback.

Do not store home addresses. Use a coarse origin zone or participant-selected public starting location.

## 8. Licensing and redistribution

### eBird

Do not redistribute raw EBD/SED records. Each collaborator who requires raw data should comply with the applicable access terms.

### Status and Trends

Do not place Status and Trends data products in a website or decision-support tool without the permissions required by current terms.

### OpenStreetMap

Provide attribution and evaluate ODbL obligations for derived route databases.

### Public repository

Safe public contents include:

- code;
- configuration templates;
- synthetic fixtures;
- aggregate metrics;
- permitted derived maps;
- documentation;
- acquisition instructions.

## 9. Model validation checklist

For each focal species:

- [ ] prevalence documented;
- [ ] complete checklists used;
- [ ] class imbalance addressed;
- [ ] effort variables included;
- [ ] time of year modeled;
- [ ] spatial holdout evaluated;
- [ ] future-time holdout evaluated;
- [ ] calibration reported;
- [ ] uncertainty coverage assessed;
- [ ] hotspot exclusion sensitivity run;
- [ ] high-volume-observer sensitivity run;
- [ ] extrapolation flagged;
- [ ] standardized protocol stated;
- [ ] ecological interpretation reviewed.

## 10. Optimization validation checklist

- [ ] utility precisely defined;
- [ ] marginal gains tested;
- [ ] candidate sites feasible;
- [ ] observation time included in budgets;
- [ ] travel data source recorded;
- [ ] exact small-instance benchmark run;
- [ ] simple baselines included;
- [ ] route stability measured;
- [ ] burden and information separated;
- [ ] accessibility frontier evaluated;
- [ ] sensitive sites excluded;
- [ ] recommendations logged.

## 11. Field-pilot checklist

- [ ] ethics or organizational review considered;
- [ ] consent language prepared;
- [ ] withdrawal process defined;
- [ ] land access verified;
- [ ] safety protocol reviewed;
- [ ] sensitive-species policy applied;
- [ ] route assignment randomized where appropriate;
- [ ] failure reasons logged;
- [ ] data-retention policy documented;
- [ ] participant results-sharing plan prepared.

## 12. Failure modes and pivots

### Not enough complete checklists

Narrow the geographic or species scope, focus on common species, or prioritize prospective structured collection.

### Uncertainty score follows density only

Publish the redundancy/coverage result and compare simple designs rather than forcing a complex active-learning claim.

### Adaptive policy does not beat environmental stratification

Emphasize that simple stratification captures most of the benefit and produce a practical low-cost method.

### Route constraints erase gains

Study the **price of human feasibility** and identify budgets at which adaptive routing becomes worthwhile.

### Volunteers decline priority routes

Test menus, micro-routes, paired outings, community hubs, or coordinated survey days.

### Observer model is unstable

Use self-reported profiles and standardized protocols rather than inferred individual scores.

### Public-app permissions are restrictive

Publish a research library and masked demonstration based on synthetic or permitted aggregate data.

## 13. Reproducibility

Every major result should include:

- frozen configuration;
- data release hash;
- software environment;
- random seeds;
- spatial split definition;
- model artifact;
- candidate-site version;
- utility version;
- figure-generation script;
- terms and citation notes.

Because raw eBird data cannot be redistributed, create a synthetic regional fixture with the same schema and known ecological truth. All tests and tutorials should run on that fixture.

## 14. Responsible-claims templates

> The model estimates the probability that a focal species would be detected on a checklist conducted under a standardized observation protocol. It does not directly estimate absolute population size.

> The information score measures expected improvement under the fitted model. A high score does not necessarily imply high conservation priority.

> Recommended routes were screened using available public-access data, but participants must follow current local rules, closures, and safety conditions.

> Observer profiles help match protocols to expected detection conditions and should not be interpreted as definitive rankings of personal expertise.

## 15. External review needs

Before field deployment, seek review from:

- an ornithologist or quantitative ecologist;
- a local birder familiar with access and seasonality;
- a parks or land-management representative;
- a privacy or research-ethics reviewer;
- an accessibility reviewer;
- a volunteer coordinator.

The project is strongest when ecological, mathematical, engineering, and community expertise genuinely constrain one another.
