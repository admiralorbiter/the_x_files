# Project Decisions and Open Questions

## Frozen v1 decisions

These choices are sufficiently resolved to begin implementation.

### D-001 — Research target
Study **institutional moral susceptibility**, not generic morality accuracy.

### D-002 — Phase 1 architecture
Use single-agent independent inference first. Multi-agent institutions are Phase 2.

### D-003 — Inference environment
Primary execution uses local/open-weight models through Ollama.

### D-004 — Model count
Pilot targets one or two models; two different families are preferred if local compute permits.

### D-005 — Model identity
Exact model names are configuration parameters and do not block implementation.

### D-006 — Human reference
Use datasets with distributions of human moral judgments when available. Human judgments are a descriptive reference, not moral truth.

### D-007 — Primary source priority
Prefer the 2026 Moral Dilemma Dataset for human-distribution baseline if accessible/licensed; use SCRUPLES as major alternative/replication source.

### D-008 — Ethical kernel
Institutional treatments must not rewrite the underlying dilemma. Store source kernel and context treatment separately.

### D-009 — Pressure families
V1 families:

1. authority;
2. personal incentive/sanction;
3. social/stakeholder;
4. organizational metric/reputation.

### D-010 — Relevance
Explicitly distinguish irrelevant pressure from normatively relevant information.

### D-011 — Intensity
Use discrete 0/1/2 intensity for v1 treatment design.

### D-012 — Direction
Treatment direction must be encoded and later tested bidirectionally.

### D-013 — Outcomes
Collect moral judgment and recommended action separately.

### D-014 — Rationales
Collect only concise observable rationale text. Hidden chain-of-thought is not a research artifact.

### D-015 — Repetition
Use repeated stochastic inference to estimate response distributions. Single completions are insufficient.

### D-016 — Pilot scale
Start with 60 stratified dilemmas and a reduced treatment screen before a full factorial expansion.

### D-017 — Domains
Education is an important starting domain, but confirmatory claims should span multiple institutional domains.

### D-018 — Prompt controls
Every pressure treatment needs a matched neutral institutional control and paraphrase robustness checks.

### D-019 — Raw data
Raw prompts and outputs are immutable and versioned by run.

### D-020 — Confirmatory boundary
Pilot is exploratory. Primary hypotheses/statistical plan must be frozen before the confirmatory scale run.

## Decisions intentionally deferred

These do **not** block v1 coding.

### O-001 — Exact Ollama models
Choose after checking local availability, runtime, model family diversity, and inference speed.

Recommended selection criteria:

- open/local availability;
- instruction-tuned chat model;
- different model families;
- reasonable generation quality;
- feasible runtime for 4k–10k calls;
- fixed quantization within each model.

### O-002 — Distributional temperature
Run smoke diagnostics at near-deterministic settings, then select a modest non-zero temperature for the distributional pilot and freeze it.

### O-003 — Replicates in confirmatory study
Five per cell is a pilot convenience. Confirmatory replication count will be chosen through simulation using pilot variance.

### O-004 — Primary statistical framework
Start with mixed-effects logistic models plus bootstrap contrasts. Decide frequentist vs Bayesian hierarchical confirmatory modeling after pilot convergence/variance diagnostics.

### O-005 — Final pressure families
All four are screened in pilot. Only the strongest and/or most theoretically important need full intensity × direction expansion.

### O-006 — Human validation of new treatment relevance
V1 can use researcher review. A later paper-quality benchmark may benefit from independent human ratings or formal annotation.

### O-007 — Release of source text
Depends on source dataset licenses. The benchmark can release source IDs + transformations if redistribution is restricted.

### O-008 — Phase 2 panel design
Do not choose consensus rules, hierarchy, number of agents, or debate protocol until Phase 1 results show which pressure mechanisms matter.

## Questions that become answerable only after the pilot

1. How large is the neutral self-consistency noise floor?
2. Which pressure family yields the largest stable effect?
3. Are high-consensus moral cases essentially immune?
4. Does the matched institutional control itself shift behavior?
5. How many scenarios rather than repetitions are needed for statistical power?
6. Do action recommendations move more than moral judgments?
7. Are model-family differences large enough to require more than two models?
8. Are some scenario domains systematically harder to construct without changing moral facts?
9. How often does the model refuse or hedge instead of selecting an option?
10. Is self-reported confidence useful or mostly noise?

## Stop/rethink criteria

Pause scale-up and redesign if:

- neutral paraphrases cause effects as large as institutional treatments;
- treatment review cannot reliably distinguish relevance categories;
- source kernels require extensive rewriting;
- output parsing remains unreliable;
- treatment conditions systematically differ in length/tone in ways that cannot be controlled;
- effect estimates are driven by fewer than a handful of scenarios;
- local model versions cannot be pinned sufficiently for reproducibility.

## Nice-to-have future decisions

- multilingual institutional pressures;
- cross-cultural role expectations;
- quantization sensitivity;
- thinking/reasoning mode comparison;
- mitigation prompts;
- adversarial institutional pressure;
- human participant comparison;
- model-mediated vs directly written pressure;
- longitudinal/multi-turn escalation;
- interaction between institutional pressure and moral framework persona.
