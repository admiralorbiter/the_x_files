# Sprint and Implementation Plan

## Planning assumptions

- Local models are served through Ollama.
- Python is the v1 orchestration/analysis language.
- The first objective is a credible pilot, not a polished app.
- Multi-agent institutions are deferred until single-agent causal effects are measured.
- Model names remain configurable until local availability/compute is confirmed.

## Milestone 0 — Research freeze and repository bootstrap

### Goal
Convert the research idea into a versioned, testable protocol.

### Tasks

- Create repository and copy documentation into `/docs`.
- Add `pyproject.toml`, formatter/linter/test configuration.
- Freeze v1 terminology: ethical kernel, institutional context, pressure family, intensity, direction, normative relevance.
- Create `PROJECT_DECISIONS.md` from the provided decisions document.
- Add source/reference bibliography.
- Add license and research-use statement.

### Acceptance criteria

- Clean test command runs.
- Every construct used in code is defined in documentation.
- No unresolved choice blocks the next milestone.

---

## Milestone 1 — Dataset acquisition and normalization

### Goal
Produce a normalized neutral moral dataset with human reference distributions.

### Tasks

1. Verify dataset availability and licenses.
2. Build adapter interface.
3. Implement Moral Dilemma Dataset adapter if accessible.
4. Implement SCRUPLES adapter.
5. Implement optional ETHICS adapter.
6. Normalize text, labels, source IDs, and human distributions.
7. Compute human entropy/disagreement.
8. Preserve original raw files untouched.
9. Generate dataset summary report.

### Deliverables

```text
data/processed/moral_baseline.parquet
results/dataset_report.md
```

### Tests

- probabilities sum correctly;
- source IDs unique;
- normalized labels reversible to source labels;
- entropy boundary tests: p=0, 0.5, 1;
- provenance is non-null.

### Acceptance criteria

- At least one human-distribution dataset is fully normalized.
- Random samples can be traced exactly to source records.
- Human-consensus strata are populated.

---

## Milestone 2 — Baseline prompt and Ollama harness

### Goal
Run neutral dilemmas repeatedly and obtain structured, resumable records.

### Tasks

- Implement Ollama health/model checks.
- Implement exact prompt renderer.
- Implement structured response schema.
- Implement parser and one standardized format retry.
- Implement immutable JSONL writer.
- Implement run manifest.
- Implement deterministic experiment plan.
- Implement resume after interruption.
- Capture model and generation metadata.

### Smoke experiment

```text
5 scenarios × 1 model × 2 replicates
```

Then:

```text
20 scenarios × 2 models × 3 replicates
```

### Acceptance criteria

- >=99% parse success after the defined retry policy on smoke data.
- Restarting a run produces no duplicate completed cells.
- Exact prompt can be reconstructed for every response.
- Raw model output is never discarded.

---

## Milestone 3 — Study 0 baseline analysis

### Goal
Characterize neutral moral distributions before any institutional manipulation.

### Tasks

- Estimate per-scenario model response probabilities.
- Compare with human distributions.
- Compute Brier/absolute error/JSD.
- Plot alignment vs human entropy.
- Measure neutral self-consistency noise.
- Compare models.
- Select candidate 60 pilot kernels.

### Acceptance criteria

- Baseline effects reproduce sensibly across repeated runs.
- High/medium/low disagreement strata are represented.
- Candidate kernels do not require substantial rewriting to add an institutional role.

### Decision gate

If baseline output is too unstable under neutral paraphrases, fix prompt protocol before continuing.

---

## Milestone 4 — Treatment authoring system

### Goal
Create valid matched institutional perturbations without altering ethical kernels.

### Tasks

- Define treatment templates for authority, incentive, social, metric/reputation.
- Define neutral institutional matches.
- Define relevant-update controls.
- Implement treatment schema.
- Implement kernel hashing.
- Implement paired-condition completeness checks.
- Author treatments for 10 development scenarios.
- Conduct blinded review.
- Revise guidelines based on failures.
- Scale to 60 pilot scenarios.

### Review rubric

Each treatment must answer:

- Does the ethical fact pattern remain unchanged?
- Is the pressure source realistic?
- Is the pressure mechanism isolated?
- Is intensity correctly tagged?
- Is direction obvious without moralizing language?
- Is relevance annotation defensible?
- Is neutral control matched?

### Acceptance criteria

- All 60 pilot kernels have valid neutral/control/treatment bundles.
- No R0 treatment adds material moral evidence.
- Every accepted treatment is frozen and hashed.

---

## Milestone 5 — Study 1 pilot pressure screen

### Goal
Detect which institutional mechanisms have measurable effects.

### Matrix

```text
60 scenarios
× 7 conditions
× 2 models
× 5 replicates
= 4,200 planned responses
```

### Conditions

- stripped neutral;
- matched institutional neutral;
- authority moderate;
- incentive moderate;
- social/stakeholder moderate;
- metric/reputation moderate;
- relevant corrective information.

### Pre-run checks

- git worktree clean;
- model digests captured;
- plan frozen;
- scenario bundle checksum frozen;
- no failed validation;
- disk space sufficient;
- 10-cell canary completes.

### Analysis

- condition effects vs matched institutional neutral;
- pressure × human entropy interaction;
- model × pressure interaction;
- relevant-information vs irrelevant-pressure response;
- parse/refusal/failure rates;
- neutral-context effect (institutional neutral vs stripped neutral).

### Acceptance criteria

- complete audit trail;
- no material condition imbalance from failed cells;
- effect estimates have scenario-level uncertainty;
- pressure-family advancement decisions are documented before Study 2.

---

## Milestone 6 — Treatment paraphrase and protocol robustness

### Goal
Determine whether pilot effects are actual pressure effects or prompt artifacts.

### Tasks

- create 2 additional paraphrases for selected conditions;
- reverse response-option order on a subset;
- duplicate neutral prompts;
- test concise vs standard protocol on a subset;
- compare effect direction/magnitude.

### Acceptance criteria

- primary candidate effects survive at least one independent paraphrase family;
- prompt protocol does not dominate the pressure effect;
- any unstable pressure family is labeled exploratory rather than confirmatory.

---

## Milestone 7 — Study 2 intensity/direction/selectivity

### Goal
Test the mechanism, not just the existence, of susceptibility.

### Tasks

- choose two pressure families based on theory + pilot;
- author low/high intensity conditions;
- author D+ and D− versions;
- create matched relevant-information conditions where logically possible;
- freeze analysis plan;
- run reduced factorial.

### Primary tests

- high > low pressure effect;
- pressure direction asymmetry;
- relevant-information update > irrelevant-pressure update;
- ambiguity moderation.

### Acceptance criteria

- intensity manipulation passes human review;
- direction pair is structurally symmetric;
- confirmatory contrasts were frozen before run.

---

## Milestone 8 — Study 3 judgment/action/rationalization

### Goal
Measure whether institutions alter recommendations even when explicit moral evaluation remains stable.

### Tasks

- add judgment-first and action-first protocols;
- add pre/post judgment protocol;
- use only a subset of strongest treatments;
- randomize protocol order at cell level;
- estimate treatment-induced judgment/action gap;
- estimate post-choice evaluative shift.

### Acceptance criteria

- order effects are separately estimated;
- no conclusion relies on hidden reasoning text;
- language distinguishes observable response rationalization from human mental-state claims.

---

## Milestone 9 — Confirmatory design and preregistration

### Goal
Convert exploratory results into a defensible confirmatory study.

### Tasks

- choose primary hypotheses;
- define SESOI;
- simulate power from pilot estimates;
- choose scenario and replicate counts;
- freeze models/model versions if possible;
- freeze prompt templates;
- freeze inclusion/exclusion rules;
- freeze primary statistical model;
- create preregistration document;
- tag repository release.

### Acceptance criteria

- no analysis flexibility on primary outcomes remains undocumented;
- exploratory analyses are explicitly separated;
- confirmatory data have not been generated before freeze.

---

## Milestone 10 — Confirmatory scale run

### Goal
Execute the preregistered design.

### Operational requirements

- immutable plan;
- canary sample;
- resumable execution;
- periodic integrity checks;
- no treatment editing during the run;
- failures recorded, not silently replaced.

### Acceptance criteria

- planned-vs-completed cell reconciliation;
- manifest complete;
- analysis can be rerun from frozen parsed output without Ollama.

---

## Milestone 11 — Cross-domain/source replication

### Goal
Show the result is not an education-prompt artifact.

### Tasks

- stratify by domain;
- replicate strongest contrasts in another source dataset;
- add at least one additional model family if compute permits;
- evaluate pressure fingerprint stability.

---

## Milestone 12 — Paper/release package

### Goal
Release a reproducible research artifact.

### Deliverables

- benchmark treatment records;
- provenance metadata;
- inference harness;
- analysis code;
- frozen configs;
- anonymized/no-sensitive raw model outputs as appropriate;
- figures/tables;
- limitations;
- model/dataset licenses;
- research paper draft;
- benchmark card.

---

# Phase 2 backlog — Multi-agent institutions

Only start after Milestones 5–8 produce interpretable single-agent effects.

Candidate experiments:

1. authority is a separate agent rather than written context;
2. private precommitment before institutional discussion;
3. dissenting peer intervention;
4. majority vs expertise manipulation;
5. consensus incentives;
6. metric-reporting agent with goal conflict;
7. hierarchical escalation chains;
8. stakeholder complaint loops;
9. institutional memory/history effects;
10. anti-conformity safeguards.

# Suggested first coding session

Implement in this order:

1. schemas;
2. dataset adapter interface;
3. one source adapter;
4. prompt renderer;
5. Ollama client;
6. parser;
7. append-only result writer;
8. deterministic plan builder;
9. smoke test;
10. baseline analysis.

Do **not** start by building treatment generation, dashboards, or multi-agent orchestration. The neutral baseline pipeline is the foundation of everything else.
