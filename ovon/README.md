# Optimal Volunteer Observation Network

**Working acronym:** OVON  
**Pilot region:** Greater Kansas City and the surrounding Missouri–Kansas landscape  
**Research mode:** Computational ecology, citizen-science design, spatial statistics, and optimization  
**Planning version:** 0.1  
**Planning date:** 2026-08-05

## Executive summary

This project asks a different question from ordinary birding or species-distribution work:

> Given a limited amount of volunteer time, where and when should people observe birds so their checklists create the most new scientific value?

The best birding location is not necessarily the best scientific sampling location. A famous wetland may produce many species and an enjoyable outing, but its next checklist may add little information because it is already sampled repeatedly. A modest park, schoolyard, floodplain, grassland edge, suburban corridor, or overlooked week in the migration season may be less exciting to an experienced birder yet more valuable scientifically.

OVON will develop and evaluate a **human-aware, route-constrained, multi-species adaptive sampling system**. The system will recommend practical observation routes that balance:

1. expected reduction in ecological uncertainty;
2. diminishing returns from repeated observations;
3. travel time and route feasibility;
4. public access, safety, and accessibility;
5. observer experience and expected detectability;
6. participant willingness and route completion;
7. seasonal priorities, particularly migration;
8. protection of sensitive species and locations.

The initial research is designed for a strong workstation rather than a large GPU cluster. The baseline uses complete eBird checklists, tabular environmental covariates, bootstrap ensembles, spatial statistics, and combinatorial optimization. Large neural models are optional extensions, not dependencies.

## Central research thesis

A useful observation network should optimize the value of an **entire portfolio of volunteer observations**, not independently rank locations.

If two nearby sites contain nearly identical habitat and model uncertainty, observing both may be redundant. A route sampling wetland, grassland, woodland, and urban habitat during a poorly observed migration week may be more useful than visiting four individually high-uncertainty sites that all answer the same question.

Let:

- \(D\) be the existing observation dataset;
- \(A\) be a proposed set of site–time–protocol observations;
- \(U(A\mid D)\) measure the expected scientific value of collecting them.

The marginal value of adding observation \(x\) is

\[
\Delta(x\mid A,D)=U(A\cup\{x\}\mid D)-U(A\mid D).
\]

A well-designed utility should usually have diminishing returns: after several similar observations are selected, another similar observation should add less value.

## Proposed research contribution

Adaptive ecological sampling, citizen-science nudges, observer-effect modeling, and informative path planning already exist as research areas. The candidate contribution is their integration into one empirically testable system.

### C1. Checklist redundancy beyond raw counts

Create a measure of how much a proposed checklist duplicates existing information after accounting for:

- spatial proximity;
- week or migration phase;
- habitat similarity;
- species assemblage;
- observation protocol and effort;
- observer or observer-profile effects.

This would distinguish “many checklists” from “many independent kinds of evidence.”

### C2. Multi-species information utility

Estimate the joint value of an observation for a portfolio of focal species or ecological guilds. The system should distinguish:

- uncertainty caused by limited sampling;
- uncertainty near habitat or range boundaries;
- uncertainty about migration timing;
- uncertainty caused by variable observer effort;
- uncertainty that could change a monitoring or conservation decision.

### C3. Human observation as part of the sensor model

Volunteers are not interchangeable sensors. A beginner and an expert can provide different expected information at the same location. The project will test whether routes can be matched to participant profiles while preserving valuable roles for beginners.

### C4. Route-constrained adaptive sampling

Select connected, practical routes under time and travel budgets rather than an unrealistic collection of disconnected optimal cells.

### C5. Rigorous offline evaluation

Build a historical-replay benchmark using held-out complete checklists, spatial and temporal blocking, and semi-synthetic known-truth experiments.

### C6. Structured field feasibility pilot

Test several short, fixed public observation points per route, with one complete stationary checklist at each stop. Repeated visits can later support detection-aware occupancy models.

## Research program

| Study | Main question | Primary output |
|---|---|---|
| A. Observation redundancy | Where is volunteer effort most repetitive? | Redundancy atlas and metric |
| B. Adaptive sampling benchmark | Which selection policy improves future prediction most efficiently? | Reproducible historical-replay benchmark |
| C. Human-aware routes | How much theoretical value survives travel, accessibility, and skill constraints? | Route optimizer and methods paper |
| D. Field feasibility | Will volunteers complete recommended standardized routes? | Pilot study and calibration dataset |
| E. Decision-aware sampling | Does reducing entropy select the same surveys as maximizing management value? | Value-of-information extension |

## Provisional pilot definition

- **Region:** 100 km radius around central Kansas City, crossing Missouri and Kansas.
- **Historical period:** 2021-01-01 through 2025-12-31.
- **Primary spatial representation:** equal-area 3 km grid; 1 km and 5 km sensitivity analyses.
- **Primary temporal representation:** ISO week, with migration-phase alternatives.
- **Primary records:** eBird Basic Dataset observations joined to Sampling Event Data.
- **Primary checklist subset:** complete stationary and plausible traveling checklists.
- **Initial species portfolio:** approximately 12 species chosen through a reproducible prevalence–seasonality–habitat procedure and ecological review.
- **Retrospective target:** standardized checklist encounter rate, not claimed true occupancy.
- **Prospective protocol:** routes of 3–5 fixed public points, each with a 10–15 minute complete stationary checklist.
- **Public application:** only after eBird terms, sensitive-species rules, and derived-product permissions are resolved.

These are starting assumptions, not irreversible commitments.

## Low-compute-first strategy

### Tier 1: workstation baseline

- `auk` in R for eBird extraction, shared-checklist collapse, and zero filling;
- DuckDB, Parquet, Polars, or data.table for analysis tables;
- generalized additive models and calibrated tree models;
- 20–50 spatial-temporal bootstrap models per focal species;
- precomputed grid, habitat, and route matrices;
- greedy selection plus insertion, swap, deletion, and 2-opt route improvement.

This tier should answer the first publishable questions.

### Tier 2: richer uncertainty and observation models

- hierarchical encounter or dynamic occupancy models;
- observer-effect models;
- latent-factor community models;
- Gaussian-process or approximate Bayesian information objectives;
- multiple-volunteer team-orienteering.

### Tier 3: optional large-scale extensions

- continental modeling;
- high-resolution remote-sensing encoders;
- deep multi-species models;
- nationwide route generation.

Tier 3 is not required for a useful contribution.

## Go/no-go gates

### Gate 1: data feasibility

Proceed when:

- EBD and Sampling Event Data access is approved;
- the regional extract contains adequate complete checklists;
- at least 8–12 focal species have enough detections across years and spatial blocks;
- public candidate sites can be identified without exposing sensitive locations.

### Gate 2: modeling feasibility

Proceed when:

- encounter-rate models are calibrated on spatial and future-time holdouts;
- uncertainty estimates distinguish well-supported from poorly supported predictions;
- results are not only a transformation of raw checklist density.

### Gate 3: optimization value

Proceed when:

- an information-aware policy outperforms random, hotspot, least-sampled, and environmental-diversity baselines in at least one predeclared outcome;
- route-aware recommendations retain useful value under realistic travel budgets;
- recommendations are stable and explainable enough for human review.

### Gate 4: field feasibility

Proceed to a larger trial when:

- volunteers understand and follow the protocol;
- recommended sites are accessible and safe;
- route completion and complete-checklist quality are acceptable;
- the pilot yields enough variance and completion information to design a powered trial.

## Immediate next actions

1. Submit a noncommercial eBird data request for records and Sampling Event Data covering Missouri and Kansas, using the project purpose precisely.
2. Record the release identifier, request language, file hash, and recommended citation.
3. Implement a synthetic mathematical kernel before the real extract arrives.
4. Identify a local quantitative ecologist or ornithologist to review species selection, closure assumptions, field protocol, and sensitive-location handling.
5. Build the redundancy audit before investing in a sophisticated ecological model.
6. Treat the first field effort as a feasibility and calibration pilot, not a definitive ecological-impact trial.

## Documentation map

- [Research landscape](docs/01_RESEARCH_LANDSCAPE.md)
- [Data plan](docs/02_DATA_PLAN.md)
- [Mathematical framework](docs/03_MATHEMATICAL_FRAMEWORK.md)
- [Experiments and hypotheses](docs/04_EXPERIMENTS_AND_HYPOTHESES.md)
- [Implementation roadmap](docs/05_IMPLEMENTATION_ROADMAP.md)
- [Validation, risks, and ethics](docs/06_VALIDATION_RISKS_AND_ETHICS.md)
- [Project decisions](docs/07_PROJECT_DECISIONS.md)
- [Annotated references](docs/08_REFERENCES.md)

## What success looks like

The strongest successful result is not merely a map of under-sampled locations. It is a validated claim such as:

> Under a fixed volunteer-time budget, a route-constrained adaptive strategy produced better-calibrated future species predictions, broader habitat and temporal coverage, or greater decision value than common alternatives, while maintaining acceptable volunteer completion and data-quality rates.

A negative result would also be useful. The project may find that simple environmental stratification performs almost as well as expensive expected-information calculations, or that travel and completion behavior erase theoretical optimization gains. Either outcome would provide practical guidance for citizen-science programs.
