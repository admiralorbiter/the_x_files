# IMPACT: Institutional Moral Pressure and Context Test

**Working project name:** IMPACT  
**Status:** Research design v1.0  
**Last literature review:** 2026-08-08  
**Primary execution environment:** local/open-weight LLMs through Ollama

## Project in one sentence

IMPACT studies whether large language models preserve, revise, or rationalize moral judgments when the **underlying ethical dilemma is held fixed** but the decision-maker is placed under controlled institutional pressures such as authority, performance metrics, incentives, peer norms, stakeholder complaints, or reputational threats.

## Central research question

> When the moral facts of a case remain constant, how do institutional pressures alter an LLM's moral judgment and recommended action, and can models selectively distinguish **normatively relevant new information** from **morally irrelevant pressure**?

This is deliberately narrower than "Are LLMs moral?" and broader than ordinary factual sycophancy. The target construct is **institutional moral susceptibility**.

## Why this project exists

Existing work has established several adjacent phenomena:

- LLM moral judgments do not perfectly reproduce distributions of human moral judgments, especially on contentious dilemmas.
- LLMs can conform to majorities, authority cues, user preferences, and other forms of social pressure.
- Moral judgments can change under narrative framing, persuasion, premise order, and multi-turn interaction.
- Role assignment and role conflict can alter model behavior.
- Moral behavior can change when strategic payoffs conflict with ethical considerations.

IMPACT therefore does **not** claim novelty from showing that context or pressure can move an LLM. Its proposed contribution is a controlled benchmark and experimental design that decomposes institutional influence into **pressure type, intensity, direction, legitimacy/relevance, role, domain, and judgment-vs-action outcome**, while keeping a matched ethical kernel constant.

## Documentation map

1. [01_RESEARCH_CHARTER.md](01_RESEARCH_CHARTER.md) — research problem, scope, questions, hypotheses, contribution claims.
2. [02_LITERATURE_KNOWLEDGE_BASE.md](02_LITERATURE_KNOWLEDGE_BASE.md) — current literature map, conceptual foundations, gap analysis.
3. [03_DATASETS_AND_SCENARIO_DESIGN.md](03_DATASETS_AND_SCENARIO_DESIGN.md) — source datasets, sampling, scenario schema, pressure taxonomy, counterfactual design.
4. [04_EXPERIMENTAL_PROTOCOL.md](04_EXPERIMENTAL_PROTOCOL.md) — exact studies, controls, randomization, prompt protocol, pilot and scale-up plans.
5. [05_MEASUREMENT_AND_STATISTICS.md](05_MEASUREMENT_AND_STATISTICS.md) — estimands, metrics, models, power/simulation strategy, robustness checks.
6. [06_IMPLEMENTATION_ARCHITECTURE.md](06_IMPLEMENTATION_ARCHITECTURE.md) — proposed repository structure, Ollama harness, data contracts, reproducibility architecture.
7. [07_SPRINT_AND_IMPLEMENTATION_PLAN.md](07_SPRINT_AND_IMPLEMENTATION_PLAN.md) — detailed staged implementation plan and acceptance criteria.
8. [08_REPRODUCIBILITY_ETHICS_AND_RISKS.md](08_REPRODUCIBILITY_ETHICS_AND_RISKS.md) — threats to validity, ethics, contamination, model/version tracking, reporting requirements.
9. [09_SCENARIO_BANK_AND_TREATMENT_EXAMPLES.md](09_SCENARIO_BANK_AND_TREATMENT_EXAMPLES.md) — worked examples spanning education and other institutional domains.
10. [10_PROJECT_DECISIONS_AND_OPEN_QUESTIONS.md](10_PROJECT_DECISIONS_AND_OPEN_QUESTIONS.md) — frozen v1 decisions and choices intentionally deferred until after pilot data.
11. [11_REFERENCES.md](11_REFERENCES.md) — research bibliography and dataset/repository links.

## Recommended study sequence

### Study 0 — Baseline moral distribution
Run one or two local models independently on moral datasets that contain human judgments. Estimate baseline model-human distributional alignment and identify high-consensus, medium-consensus, and high-disagreement dilemmas.

### Study 1 — Controlled institutional pressure
For a stratified subset of moral dilemmas, hold the ethical kernel constant and append controlled institutional context. Test authority, incentives, social pressure, and metric/reputation pressure against matched neutral controls.

### Study 2 — Selective updating and directionality
Test whether models respond differently to morally relevant information versus irrelevant pressure, and whether they are equally movable toward and away from the baseline moral position.

### Study 3 — Judgment/action/rationalization
Separate explicit moral evaluation from recommended action. Test whether pressure changes action more than judgment and whether committing to an action changes the model's later moral evaluation.

### Study 4 — Generalization
Replicate the strongest effects across model families, domains, prompt paraphrases, sampling parameters, and source datasets.

### Phase 2 — Multi-agent institutions
Only after single-agent causal effects are established, instantiate principals, peers, stakeholders, and decision-makers as separate agents and examine how institutional structure produces pressure endogenously.

## V1 pilot target

The first computational pilot is intentionally moderate:

- **60 dilemmas**, stratified by human disagreement.
- **2 local models** from different families when practical; model names remain configuration, not methodology.
- **Core conditions:** neutral baseline, matched institutional control, four pressure families, one legitimate-update control.
- **Repeated stochastic draws** per model × dilemma × condition.
- Expand intensity and direction only after confirming that the treatment generator and response parser are reliable.

The project should prefer a **smaller clean factorial design** over thousands of weakly controlled prompt variants.

## Research principles

1. **Hold the ethical kernel fixed.** Treatment prompts should add institutional information rather than rewrite the core dilemma.
2. **Separate pressure from evidence.** Robustness means resisting irrelevant pressure while updating to relevant facts—not refusing to update.
3. **Measure distributions, not anecdotes.** Repeated inference is part of the experiment.
4. **Record behavior before explanations.** Require a constrained judgment/action field before any short rationale to reduce parser and verbosity effects.
5. **Do not use hidden chain-of-thought as data.** Store observable answers, concise justifications, treatment metadata, and inference metadata.
6. **Pre-register primary outcomes before the scale run.** The exploratory pilot is for design validation and effect-size estimation.
7. **Keep Phase 1 single-agent.** Multi-agent deliberation is a separate causal layer.

## Immediate build target

A successful v1 repository should be able to execute:

```bash
python -m impact.cli validate-data
python -m impact.cli build-pilot --config configs/pilot.yaml
python -m impact.cli run --config configs/pilot.yaml
python -m impact.cli validate-runs --run-id <RUN_ID>
python -m impact.cli analyze --run-id <RUN_ID>
```

and produce immutable JSONL/Parquet run records, summary tables, diagnostic plots, and a machine-readable manifest containing model digests, Ollama version, prompts, seeds, temperatures, dataset versions, and git commit.

## Definition of success for the first milestone

The pilot is successful if it demonstrates that we can:

- reproduce a stable neutral baseline;
- produce matched treatment pairs without altering the ethical kernel;
- parse at least 99% of responses without manual intervention;
- estimate within-dilemma pressure effects with uncertainty;
- distinguish treatment effects from paraphrase/protocol noise;
- identify which pressure families deserve a preregistered scale-up.
