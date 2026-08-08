# Experiments and Metrics

## 1. Two-track experimental strategy

### Track A — exploration

The first weeks should optimize for discovery.

Run worlds, inspect surprising events, change assumptions, and generate hypotheses. Preserve traces so discoveries can later be reconstructed.

### Track B — publishable comparisons

Once interesting behaviors recur, freeze the scenario and compare controlled architectural variants.

The biggest mistake would be to make the first playable build so constrained that it suppresses the phenomena we are trying to discover.

## 2. Immediate playful experiments

### Experiment P1 — Blank society century

Run 100 actors for 100 simulated years with minimal institutions.

Question:

> What organizational structures appear without explicit organization templates?

Record all new roles/institutions and their ancestry.

### Experiment P2 — Recursive cognition

Fork the same world at initialization:

- Branch A: agents cannot spawn sub-agents.
- Branch B: agents can spawn bounded temporary sub-agents.

Watch for differences in:

- solution diversity;
- institutional complexity;
- computational cost;
- help-seeking;
- ability to recover from shocks;
- bureaucracy/runaway delegation.

### Experiment P3 — Fragile memory world

Make artifacts decay or become contradictory.

Question:

> Does the society invent archives, verification, trusted roles, redundancy, or memory rituals without being told to?

### Experiment P4 — Unknown environmental rule change

Change a world parameter at Year 20 without telling agents what changed.

Question:

> Does the society detect a change, seek evidence, and alter institutions?

### Experiment P5 — Foreign capability

Introduce a capability the society does not initially possess, but make it discoverable through help-seeking.

Question:

> Which agents learn to ask for help, and does the behavior diffuse?

## 3. Candidate publishable experiments

### E1 — Recursive organization versus flat organization

**Hypothesis:** bounded recursive delegation improves performance on decomposable tasks and shock adaptation up to a depth/cost threshold, after which coordination overhead dominates.

Independent variable:

- no delegation;
- one-level delegation;
- recursive delegation depth 2–4.

Primary outcomes:

- validated task value;
- shock recovery time;
- compute cost;
- duplicated work;
- delegation depth;
- failed subtrees.

### E2 — Help-seeking as an explicit capability

Compare:

- no help action;
- help only when a tool call fails;
- explicit uncertainty/blocker-driven help-seeking.

Outcomes:

- unresolved blockers;
- hallucinated/unsupported actions;
- task success;
- cost and latency;
- repeated errors.

### E3 — Emergence capture without goal drift

Compare memory strategies:

- store only task results;
- store all reflections;
- candidate → evidence → institutionalization pipeline.

Question:

> Can the system preserve useful emergent procedures without allowing every interesting observation to rewrite organizational policy?

### E4 — Organization mutates itself

Allow one condition to change organizational structure and another to use a fixed structure.

Measure whether structural mutations improve future outcomes and whether successful structures recur across seeds.

### E5 — Autonomous shock discovery in district replay

Compare:

- baseline forecasting only;
- anomaly detection without external research;
- anomaly detection + autonomous boundary scanning + validated shock features.

Primary outcomes:

- post-break forecast skill;
- detection delay;
- false shock rate;
- evidence precision;
- interval calibration;
- hindsight violations.

### E6 — Same model, different harness

Hold the Ollama model fixed while changing:

- durable external state;
- recursive delegation;
- verification;
- help-seeking;
- context strategy.

This connects directly to current harness research and prevents all improvements from being attributed to model size.

## 4. Metrics: organizational behavior

### Agent birth and retirement

- births per simulated year;
- temporary/persistent ratio;
- median lifetime;
- lineage depth distribution;
- descendants per parent.

### Delegation

- delegation rate;
- task completion after delegation;
- return-contract failures;
- duplicate subtask rate;
- compute per completed delegated task.

### Help

- help requests per 100 active tasks;
- routing success;
- median resolution delay;
- help ROI;
- repeated unresolved requests.

### Institutions

- birth rate;
- survival curve;
- membership turnover;
- resource share;
- authority concentration;
- number of child institutions;
- rule change frequency.

### Knowledge

- artifact reuse;
- number of downstream citations;
- contradictions discovered;
- stale procedure reuse;
- procedure adoption and abandonment.

### Coordination

- blocked dependency time;
- duplicate work;
- messages per useful state transition;
- proportion of actions requiring clarification;
- idle/drift periods.

## 5. Metrics: emergence

Emergence is multidimensional.

### Novel institution rate

Count institutions with structural features not previously seen in the same run.

### Independent convergence

Two lineages independently develop similar role/procedure/institution patterns.

This is especially interesting because it suggests environmental pressure rather than a single prompt accident.

### Adoption diffusion

For artifact/procedure \(k\), model adoption over time:

\[
A_k(t)=\#\{agents/institutions\ using\ k\ at\ t\}.
\]

### Persistence after creator exit

A powerful indicator of institutionalization:

\[
Persistence_k = t_{last\ use} - t_{creator\ retirement}.
\]

### Structural diversity

Use role/institution distributions, graph motifs, and community structures rather than only an LLM novelty rating.

## 6. Metrics: resilience and external pressure

- anomaly detection delay;
- time to first explicit external-change hypothesis;
- time to behavioral adaptation;
- performance drop magnitude;
- recovery time;
- permanent regime change versus recovery;
- number of obsolete assumptions retired;
- new capabilities acquired after shock.

## 7. Metrics: model/harness reliability

- structured-output validation rate;
- tool-request validity rate;
- retries per invocation;
- timeout rate;
- schema-repair rate;
- agent self-claimed completion versus external completion;
- stale-context incidents;
- repeated-state loops;
- runner recovery success;
- events lost after crash (target: zero committed events).

## 8. Compute accounting

Local inference is not free merely because there is no API bill.

Track:

- wall time;
- model load time;
- prompt tokens / generated tokens if available;
- invocation count;
- GPU utilization snapshots if convenient;
- energy proxy if available;
- context length;
- parallelism;
- accepted-state-change per invocation;
- useful artifact per compute-hour.

A useful metric:

\[
ComputeEfficiency=\frac{ValidatedValue}{GPUHours}.
\]

For Society Lab, “ValidatedValue” can be scenario-specific and exploratory; do not pretend it is universally objective.

## 9. Statistical design for later confirmatory studies

Use multiple sources of randomness:

- world seed;
- model seed where supported;
- scenario perturbations.

A basic hierarchical model can separate run-to-run and scenario effects.

For outcome \(y\):

\[
y_{ijk}=\beta_0+\beta_1 Treatment_i+\beta_2 Horizon_j+\beta_3 Treatment_iHorizon_j+u_k+\epsilon_{ijk}
\]

where \(u_k\) is a scenario/seed random effect.

For time-to-collapse or time-to-recovery, use survival analysis.

For binary completion, use logistic mixed models.

For forecast comparisons, use paired errors at common replay origins and bootstrap confidence intervals.

## 10. Avoid Goodharting emergence

Do not expose a single `emergence_score` to agents as an optimization target.

If agents are rewarded for novelty, they can produce pointless churn, rename roles constantly, or manufacture institutions.

Instead:

- keep emergence metrics observer-side;
- use them to surface interesting runs;
- evaluate persistence and downstream use;
- ask whether a structure affected world outcomes;
- preserve boring runs as valid negative evidence.

## 11. Research logs

Every exploratory observation worth remembering gets a lightweight record:

```yaml
observation_id: obs_...
run_id: run_...
branch_id: br_...
claim: Temporary specialist agents repeatedly became neutral mediators.
evidence_events: [...]
first_noticed: 2026-08-10
status: exploratory
possible_experiment: Compare recursive spawning on/off across 20 seeds.
```

That creates a clean bridge from “whoa, look at that” to a future paper.
