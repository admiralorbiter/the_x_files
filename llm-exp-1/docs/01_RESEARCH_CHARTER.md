# Research Charter

## Working title

**IMPACT: Institutional Moral Pressure and Context Test — Measuring Selective Moral Susceptibility in Large Language Models**

Alternative paper-style title:

> **When Institutions Lean on the Model: Controlled Effects of Authority, Incentives, Social Pressure, and Metrics on LLM Moral Decisions**

## 1. Problem statement

Large language models increasingly act as advisers, evaluators, and agents inside organizations. In real institutions, decision-makers rarely confront moral choices in a vacuum. A teacher may face pressure from administrators and parents; a clinician may face resource constraints and throughput targets; a hiring manager may face executive preferences and diversity goals; a nonprofit manager may face donor expectations and output metrics.

These institutional facts can be of two fundamentally different kinds:

1. **Normatively relevant information** that should rationally affect a decision—for example, discovering a grading error, learning that a policy requires a particular procedure, or receiving new evidence about likely harm.
2. **Normatively irrelevant or coercive pressure** that changes the decision-maker's incentives without changing the moral facts—for example, a supervisor preferring a convenient outcome, a performance metric rewarding a questionable action, or a stakeholder threatening a complaint.

A reliable moral decision-support system should not simply be invariant. It should demonstrate **selective updating**: responsiveness to relevant information and resistance to irrelevant pressure.

## 2. Target construct

### Institutional moral susceptibility

For model \(m\), scenario \(i\), treatment \(t\), and response outcome \(Y\):

\[
S_{mit} = P(Y=1 \mid i,m,t) - P(Y=1 \mid i,m,\text{neutral})
\]

where the treatment changes the institutional context while the ethical kernel of scenario \(i\) remains fixed.

Susceptibility is not automatically failure. The interpretation depends on the normative relevance and direction of the treatment.

### Selective moral updating

A model exhibits selective updating when it is comparatively responsive to relevant information while comparatively resistant to irrelevant pressure.

Conceptually:

\[
\text{Selective Updating}
= \text{Response}_{\text{relevant}}
- \text{Response}_{\text{irrelevant}}
\]

The exact operationalization is specified in the statistics document.

## 3. Primary research questions

### RQ1 — Baseline alignment
How closely do selected local/open-weight models reproduce human moral judgment distributions in neutral conditions?

### RQ2 — Pressure susceptibility
When the ethical kernel is held fixed, which institutional pressure mechanisms shift model moral judgments or recommended actions?

### RQ3 — Dose response
Does susceptibility increase monotonically with the intensity of authority, incentive, social, or metric pressure?

### RQ4 — Selective updating
Can models distinguish legitimate new evidence/policy context from institutionally powerful but normatively irrelevant pressure?

### RQ5 — Directionality
Are models equally susceptible when pressure pushes toward versus away from their neutral modal judgment, or is compliance directionally asymmetric?

### RQ6 — Moral ambiguity
Does institutional susceptibility increase as the underlying human judgment distribution becomes more divided?

### RQ7 — Judgment versus action
Does pressure affect a model's recommended action more strongly than its explicit moral evaluation?

### RQ8 — Post-choice rationalization
After a model chooses a pressure-consistent action, does its subsequent moral evaluation shift toward justifying that action?

### RQ9 — Model fingerprints
Do different model families exhibit stable, interpretable institutional susceptibility profiles—for example, high authority sensitivity but low peer sensitivity?

### RQ10 — Domain generalization
Do pressure effects transfer across education, healthcare, hiring/workplace, public administration, and resource-allocation contexts?

## 4. Primary hypotheses

### H1 — Pressure effect
Normatively irrelevant institutional pressure will shift model decisions relative to matched neutral controls.

### H2 — Ambiguity amplification
Pressure susceptibility will increase with human moral disagreement.

For binary human judgments with probability \(p_i\):

\[
H_i = -p_i\log p_i -(1-p_i)\log(1-p_i)
\]

and we expect, for irrelevant-pressure treatments:

\[
\frac{\partial |S|}{\partial H_i} > 0.
\]

### H3 — Intensity gradient
High-intensity pressure will produce a larger absolute treatment effect than low-intensity pressure within the same pressure family.

### H4 — Selective updating
Models will update more appropriately when treatment information is normatively relevant than when equivalent-length context is normatively irrelevant.

### H5 — Judgment/action dissociation
Institutional pressure will have a larger effect on recommended action than on explicit moral acceptability judgments.

### H6 — Rationalization
Conditional on making a pressure-consistent choice, post-choice moral evaluation will move toward that choice relative to pre-choice evaluation.

### H7 — Model-specific susceptibility
Model-family × pressure-family interactions will be non-zero and replicable across scenario subsets.

### H8 — Protocol moderation
Effects will survive prompt paraphrases and matched controls, although absolute flip rates may vary with evaluation protocol.

## 5. Claims we should not make

The study should not claim that:

- an LLM "has morals" in a human psychological sense;
- human majority judgment is moral truth;
- any answer change is a failure;
- chain-of-thought text reveals the model's true internal reasoning;
- resistance to pressure is always desirable;
- this is the first demonstration of LLM sycophancy, conformity, role effects, moral instability, or payoff-sensitive moral behavior.

## 6. Proposed contribution

A defensible contribution is the combination of:

1. **Ethical-kernel-preserving counterfactuals:** the moral case is fixed while institutional context is manipulated.
2. **Institutional pressure taxonomy:** authority, incentives, social/stakeholder pressure, and metrics/reputation are treated as separable mechanisms.
3. **Pressure intensity:** treatments support dose-response analysis rather than only binary perturbations.
4. **Treatment direction:** pressure can push toward or away from a baseline decision.
5. **Normative relevance:** relevant evidence is explicitly distinguished from irrelevant coercion.
6. **Judgment/action separation:** explicit moral evaluation and recommended action are analyzed separately.
7. **Human-distribution anchoring:** scenario ambiguity and baseline alignment are connected to human judgment distributions when available.
8. **Open local reproducibility:** the core benchmark is designed for open-weight models through Ollama rather than requiring proprietary APIs.
9. **Institutional susceptibility profiles:** models can be compared as vectors of sensitivity across mechanisms rather than reduced to one ethics score.
10. **Phase-separated multi-agent extension:** causal single-agent treatment effects are established before institutions are implemented as interacting agents.

## 7. Scope

### In scope for v1

- English-language text-only prompts.
- One- or two-model exploratory pilot.
- Open/local execution through Ollama.
- Binary or constrained categorical moral decisions.
- Human-distribution moral datasets as source/reference material.
- Education plus several non-education institutional domains.
- Short, observable rationales collected after a structured response.
- Repeated stochastic inference.

### Out of scope for v1

- Training or fine-tuning models.
- Human-subject data collection.
- Hidden chain-of-thought analysis.
- Autonomous real-world decision-making.
- Claims about legal or professional correctness.
- Full multi-agent organizations.
- Multilingual/cross-cultural replication.
- Demographic-persona manipulation unless explicitly added as a later preregistered study.

## 8. Unit of analysis

The atomic inference record is:

\[
(\text{scenario},\text{model},\text{condition},\text{prompt variant},\text{replicate},\text{seed/config})
\]

The primary causal comparison is **within scenario**, not across unrelated scenarios.

## 9. Paper-level story

The preferred narrative is:

1. Establish what the model does in neutral moral cases and how that compares with human distributions.
2. Preserve those cases while introducing institutional pressure.
3. Show which pressures matter, under what ambiguity, and at what intensity.
4. Demonstrate whether models distinguish evidence from pressure.
5. Separate moral judgment from behavior/recommendation.
6. Characterize model-specific susceptibility profiles.
7. Only then ask whether multi-agent institutions amplify or mitigate those susceptibilities.

## 10. Falsification-friendly outcomes

The project remains useful if the main pressure effects are small. Possible meaningful null/negative results include:

- local instruction-tuned models are robust to institutional pressure after matched controls;
- apparent pressure effects vanish once prompt-length and protocol controls are introduced;
- only human-ambiguous dilemmas show effects;
- action recommendations move but moral judgments do not;
- models update indiscriminately to both relevant and irrelevant cues;
- model-family differences dominate institutional differences;
- within-model sampling variance is large enough to make naive flip-rate conclusions unreliable.

The analysis and documentation should preserve these possibilities rather than optimize prompts to create dramatic effects.
