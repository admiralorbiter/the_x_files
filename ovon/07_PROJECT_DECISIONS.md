# Project Decisions and Open Questions

This document records provisional research and architecture decisions. Decisions can change, but changes should be explicit and traceable.

## ADR-001: Use encounter rate as the retrospective MVP target

**Status:** Provisionally accepted

**Decision:** Model the probability of detecting a species on a standardized complete checklist.

**Rationale:**

- historical eBird records are not a controlled repeat-visit design;
- absolute detection and occupancy are generally not separately identified from opportunistic visits alone;
- Cornell’s best-practices workflow supports encounter-rate estimation;
- encounter models are computationally manageable.

**Consequence:** Do not label retrospective predictions true occupancy.

**Future:** Use occupancy models for structured repeated field sites.

---

## ADR-002: Use a Kansas City regional pilot

**Status:** Provisionally accepted

**Decision:** Begin with a 100 km radius around Kansas City and buffer the ecological fitting area.

**Rationale:**

- local application;
- manageable computation;
- diverse habitat and urbanization;
- cross-state context;
- feasible field routes.

**Open item:** Freeze the center coordinate and boundary after preliminary coverage review.

---

## ADR-003: Freeze historical outcomes at 2025-12-31

**Status:** Accepted

**Decision:** Use complete years 2021–2025 for the primary benchmark.

**Rationale:** Avoid partial-year bias and enable clean rolling future-year evaluation.

**Consequence:** Newer records may support prospective or external checks but should not silently enter the frozen benchmark.

---

## ADR-004: Use complete stationary and traveling checklists

**Status:** Accepted

**Decision:** Infer focal-species non-detections only from complete checklists.

**Sensitivity:** Compare with stationary-only and short-distance traveling subsets.

---

## ADR-005: Separate scientific utility from volunteer utility

**Status:** Accepted

**Decision:** Report scientific information, route burden, expected completion, accessibility, and participant learning or interest separately.

**Rationale:** These objectives can conflict and should not be hidden inside one opaque score.

---

## ADR-006: Start with an approximate transparent information utility

**Status:** Accepted

**Decision:** The MVP will use bootstrap disagreement plus ecological–spatiotemporal redundancy instead of exact Bayesian expected information gain.

**Rationale:**

- lower compute;
- easier debugging;
- easier explanation;
- direct ablations;
- avoids repeated posterior updates for every hypothetical outcome.

**Benchmark:** Compare with GP mutual information or D-optimal design on smaller problems.

---

## ADR-007: Use routes of short stationary checklists in field work

**Status:** Recommended; ecological review required

**Decision:** Each route contains several fixed 10–15 minute stationary stops, with one complete checklist per stop.

**Rationale:** Better spatial precision, repeatability, occupancy extension, and beginner instructions.

**Alternative:** One long traveling checklist.

**Reason not preferred:** Ambiguous spatial support and weaker repeat-visit interpretation.

---

## ADR-008: No public individual observer ranking

**Status:** Accepted

**Decision:** Observer effects may be modeled privately for ecological inference, but individual skill scores will not be published or gamified.

---

## ADR-009: Status and Trends are validation inputs, not default application layers

**Status:** Accepted

**Decision:** Use Status and Trends only under current terms, primarily for research comparison or permitted simulation.

**Rationale:** Current terms restrict web and decision-support use without prior consent.

---

## ADR-010: Access, safety, and sensitive-species rules are hard constraints

**Status:** Accepted

**Decision:** The optimizer cannot trade legal access, field safety, or species protection for higher expected information.

---

## ADR-011: Use a rule-selected multi-species portfolio

**Status:** Provisionally accepted

**Decision:** Begin with approximately 12 species spanning common residents, migrants, habitat specialists, and different detection difficulty.

**Open item:** Freeze thresholds after data audit and ecological review.

---

## ADR-012: Evaluate adaptive sampling in three modes

**Status:** Accepted

**Decision:** Use:

1. held-out real checklist replay;
2. cell-week candidate/reference splits;
3. semi-synthetic known truth.

**Rationale:** No single retrospective design supplies all counterfactual outcomes.

---

## ADR-013: Log recommendation policies

**Status:** Accepted

**Decision:** Store model version, utility version, candidate set, routes offered, participant choice, and completion.

**Rationale:** Adaptive recommendations alter the future observation process.

---

## ADR-014: Maintain a low-compute baseline permanently

**Status:** Accepted

**Decision:** Every major experiment must run in a workstation-scale development configuration.

**Rationale:** The contribution should not depend on costly neural inference.

---

## ADR-015: Treat simple methods as serious competitors

**Status:** Accepted

**Decision:** Environmental stratification, equal-area sampling, and least-sampled routing are primary baselines, not straw men.

**Rationale:** A result showing that simple sampling captures most of the value would itself be useful.

---

# Open questions

## Q1. What is the first ecological target?

Candidates:

1. year-round encounter maps;
2. migration-week encounter maps;
3. habitat-boundary uncertainty;
4. permanent-monitoring network design.

**Recommendation:** Begin with migration-week encounter maps for a mixed portfolio and use residents as a stability baseline.

## Q2. What spatial representation is best?

Candidates:

- 1 km grid;
- 3 km grid;
- 5 km grid;
- H3 cells;
- fixed public sites only.

**Recommendation:** 3 km equal-area baseline, multiscale habitat covariates, and fixed sites for field work.

## Q3. How should species be weighted?

Candidates:

- equal;
- equal within guild;
- conservation priority;
- management decision value;
- inverse prevalence.

**Recommendation:** Equal within guild for MVP, with sensitivity analyses. Avoid unstable inverse-prevalence weights for rare species.

## Q4. Should observer ID enter the first model?

**Recommendation:** Not required for the first atlas. Add private observer-level sensitivity analyses and prospective self-reported profiles later.

## Q5. What is the practical route origin?

Candidates:

- fixed community hubs;
- coarse participant zone;
- user-selected origin;
- park-and-ride locations.

**Recommendation:** Fixed hubs for research benchmarks and participant-selected origins for later deployment. Never store home addresses.

## Q6. Should every kind of uncertainty be rewarded?

**Recommendation:** No. Compare predictive entropy, model disagreement, and decision value. Flag extrapolation rather than automatically treating it as useful.

## Q7. How many volunteers are required?

The first field effort is a feasibility pilot. Use observed acceptance, completion, and within-participant variance to design a later powered study rather than inventing a precise confirmatory sample now.

## Q8. What counts as a successful contribution?

At least one of:

- a validated redundancy metric;
- an adaptive policy outperforming strong baselines;
- a route algorithm with a guarantee or compelling empirical performance;
- a quantified price of human feasibility;
- an informative field-pilot result, including a negative result.

## Q9. Should the public product recommend exact sites?

**Recommendation:** Not initially. Start with private research routes and public aggregate maps. Exact public recommendations require access, safety, licensing, and sensitive-species review.

## Decision template

```markdown
## ADR-XXX: Decision title

**Date:** YYYY-MM-DD  
**Status:** Proposed / Accepted / Superseded / Rejected

**Context:**

**Decision:**

**Alternatives:**

**Evidence:**

**Consequences:**

**Revisit trigger:**
```
