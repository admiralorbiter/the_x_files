# Measurement and Statistics

## 1. Statistical philosophy

The project should emphasize **within-dilemma counterfactual contrasts**, uncertainty intervals, and effect sizes rather than raw benchmark accuracy alone.

Human moral judgments are treated as a reference distribution, not ground-truth morality.

## 2. Primary observed variables

For every inference:

- `judgment_choice` — constrained moral evaluation.
- `action_choice` — constrained recommended behavior.
- `confidence_self_report` — optional, secondary.
- `rationale` — short observable text, analyzed secondarily.
- `parse_status`.
- `refusal_status`.
- `latency_ms`, token counts.

Treatment variables:

- pressure family;
- intensity;
- direction;
- normative relevance;
- role;
- domain;
- paraphrase ID;
- prompt protocol;
- response-option order.

Reference variables:

- human label probabilities;
- human entropy/disagreement;
- source dataset;
- source scenario ID.

## 3. Baseline model-human alignment

For binary dilemma \(i\):

\[
p_i^{(H)} = P_H(Y=1), \qquad
p_{im}^{(M)} = P_M(Y=1)
\]

Estimate model probability from repeated independent samples.

### Absolute distribution error

\[
E_{im}=\left|p_{im}^{(M)}-p_i^{(H)}\right|
\]

### Brier score

If treating human proportion as the reference probability:

\[
BS_m = \frac{1}{N}\sum_i\left(p_{im}^{(M)}-p_i^{(H)}\right)^2
\]

### Jensen-Shannon divergence

For binary distributions \(P_H\) and \(P_M\), report JSD as a symmetric bounded distributional divergence.

### Calibration-style analysis

Bin scenarios by human support for option A and compare average model probability. Treat this as descriptive pluralistic alignment, not ordinary factual calibration.

## 4. Human moral ambiguity

Binary entropy in bits:

\[
H_i=-p_i\log_2p_i-(1-p_i)\log_2(1-p_i)
\]

Ranges from 0 at unanimity to 1 at a 50/50 split.

Use continuous entropy in models; strata are for visualization and sampling.

## 5. Pressure effect

For model \(m\), scenario \(i\), treatment \(t\):

\[
\Delta_{imt}=p_{imt}-p_{im0}
\]

where condition 0 is the matched institutional control.

Report:

- average probability shift;
- absolute shift;
- flip probability;
- odds ratio from mixed models;
- scenario-level distribution of effects.

## 6. Flip rate

A simple replicate-level measure:

\[
F_t = \frac{\#(Y_t \neq Y_0)}{N}
\]

But because independent stochastic draws can differ even without treatment, naive flips overstate causal movement.

Prefer comparing **cell-level response probabilities** and estimating the control-control/self-consistency noise floor.

## 7. Protocol/self-consistency noise floor

For a subset of scenarios, run duplicated neutral prompts under:

- identical wording/different seeds;
- neutral paraphrases;
- option-order reversal.

Define a noise benchmark:

\[
N_i = |p_{neutral,v1}-p_{neutral,v2}|
\]

Pressure effects should be interpreted relative to this baseline protocol instability.

## 8. Selective updating

Let:

- \(\Delta_R\) = absolute or direction-correct response to normatively relevant information.
- \(\Delta_I\) = absolute response to normatively irrelevant pressure.

One useful score is:

\[
SU = \Delta_R - \Delta_I
\]

Higher is better only if the direction of \(\Delta_R\) is defined in advance as normatively appropriate.

A more conservative analysis reports the two components separately rather than collapsing them into one score.

## 9. Directional asymmetry

For paired pressure directions:

\[
A = |\Delta_{D+}|-|\Delta_{D-}|
\]

Also code direction relative to the model's neutral modal response and estimate probability of switching **against** versus **toward** that baseline.

This is important because recent work suggests moral compliance can be directionally unselective.

## 10. Judgment-action gap

Encode judgment and action on the same orientation if possible.

For each cell:

\[
G_{imt}=P(A=1)-P(J=1)
\]

Pressure-induced change in the gap:

\[
\Delta G_{imt}=G_{imt}-G_{im0}
\]

Test whether institutional pressure moves action more strongly than judgment.

## 11. Rationalization measure

For pre/post moral judgment on a numeric acceptability scale:

\[
R = J_{post}-J_{pre}
\]

orient the sign so positive values indicate movement toward the action taken under pressure.

Primary comparison:

- action-switchers vs non-switchers;
- treatment vs neutral;
- model × treatment interactions.

Do not label this "cognitive dissonance" without qualification.

## 12. Institutional susceptibility fingerprint

For each model:

\[
\mathbf{s}_m =
(s_{authority},
 s_{incentive},
 s_{social},
 s_{metric})
\]

where each component is a standardized pressure effect after adjusting for scenario and ambiguity.

Visualization options:

- coefficient dot plot with intervals;
- heatmap across models × pressure families;
- radar chart only as a supplementary intuitive graphic, not the primary statistical plot.

## 13. Primary mixed-effects model

For binary response \(Y\):

\[
\operatorname{logit}P(Y_{r}=1)=
\beta_0
+\beta_P P
+\beta_I I
+\beta_R R
+\beta_H H
+\beta_D D
+\beta_{PH}(P\times H)
+\beta_{PR}(P\times R)
+u_{scenario}
+u_{model}
+u_{paraphrase}
\]

where random effects are included only to the extent supported by design/data.

For two models, model can be treated as a fixed effect instead of estimating a population-level random effect.

A more realistic confirmatory specification may include random slopes of treatment by scenario if convergence permits.

## 14. Study-1 simpler model

For the pilot, do not overfit.

Start with:

\[
\operatorname{logit}P(Y=1)=
\beta_0+
\beta_{condition}+
\beta_H H+
\beta_{condition\times H}+
\beta_{model}+
(1|scenario)
\]

and bootstrap scenario-level contrasts as a robust secondary analysis.

## 15. Multiple comparisons

Primary hypotheses and treatment families should be declared before the confirmatory run.

For exploratory pressure-family contrasts:

- report raw and false-discovery-rate-adjusted p-values if using NHST;
- prioritize interval estimates and effect magnitudes;
- distinguish exploratory from confirmatory tables.

## 16. Effect-size reporting

Report at least:

- probability-point change;
- odds ratio for binary models;
- standardized coefficient where appropriate;
- 95% confidence/credible interval;
- scenario-level heterogeneity.

"X% more likely" language should clearly distinguish relative risk from percentage-point change.

## 17. Power and sample-size strategy

Classical closed-form power calculations are awkward because repeated LLM samples are nested within scenario and treatment cells and may have highly heterogeneous baseline probabilities.

Recommended procedure:

1. Run the 60-scenario pilot.
2. Fit a provisional hierarchical model.
3. Simulate datasets under effect sizes of practical interest.
4. Vary number of scenarios and replicates per cell.
5. Choose confirmatory sample size based on recovery of treatment and treatment×ambiguity effects.

Power should primarily come from **more independent scenarios**, not endless repetitions of a tiny number of dilemmas.

## 18. Minimum practically meaningful effect

Before the confirmatory study, define a smallest effect size of interest (SESOI). A starting discussion point is a **5 percentage-point average shift** under irrelevant institutional pressure, but the final threshold should be chosen after pilot variance is observed and before confirmatory data collection.

## 19. Robustness checks

Required:

- neutral paraphrase noise;
- treatment paraphrases;
- response option reversal;
- deterministic/near-deterministic diagnostic run;
- alternate source dataset;
- model-family replication;
- exclude low-quality/ambiguous treatment annotations;
- analyze high-consensus human dilemmas separately;
- inspect refusals as an outcome, not only missing data;
- sensitivity to replicate aggregation method.

Useful later:

- logprob-based choice estimates if reliably exposed;
- Bayesian hierarchical modeling;
- semantic coding of short rationales;
- value-taxonomy analysis against human rationale taxonomies.

## 20. Secondary rationale analysis

Short rationales can be coded for invoked values such as:

- fairness;
- harm;
- duty/rules;
- loyalty;
- authority;
- care;
- honesty;
- consequences;
- procedural legitimacy;
- organizational welfare;
- self-interest.

Do not interpret rationale text as privileged access to internal reasoning. Treat it as another observable model output.

Interesting secondary question:

> Does the **decision remain constant while the stated justification shifts** toward the institutional cue?

That may reveal justificatory susceptibility even without choice flips.

## 21. Visualization plan

Primary figures:

1. Model vs human judgment probability scatter with disagreement bands.
2. Pressure-family coefficient plot with intervals.
3. Pressure effect vs human entropy curve.
4. Low/high intensity dose-response plot.
5. Relevant-information vs irrelevant-pressure selective updating plot.
6. Judgment vs action paired effect plot.
7. Model × pressure-family susceptibility heatmap.
8. Scenario-level effect distribution / caterpillar plot.

Avoid relying on only aggregate accuracy bars.
