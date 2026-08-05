# Mathematical Framework

## 1. Purpose

This document turns “send volunteers to under-observed locations” into a defined optimization problem. It separates:

1. ecological state;
2. observation and detection process;
3. uncertainty about the state;
4. scientific or decision utility;
5. volunteer capability and completion;
6. route feasibility.

Collapsing these components into a single heuristic score would make the system difficult to validate and easy to misinterpret.

## 2. Notation

Let:

- \(s\in\mathcal S\): species;
- \(i\in\mathcal I\): spatial cell or fixed site;
- \(t\in\mathcal T\): week or survey period;
- \(j\): checklist visit;
- \(o\in\mathcal O\): observer or observer profile;
- \(x_{it}\): environmental and seasonal variables;
- \(e_j\): observation-effort variables;
- \(y_{sijt}\in\{0,1\}\): detection indicator;
- \(c_{sijt}\): reported count;
- \(D\): existing data;
- \(A\): proposed new observations;
- \(R\): ordered route of observation stops;
- \(\theta\): ecological and observation-model parameters.

## 3. Observation-density and redundancy measures

### 3.1 Raw checklist density

\[
N_{it}=\sum_j\mathbf 1\{j\text{ occurs in }(i,t)\}.
\]

This is descriptive but insufficient. A checklist in a new habitat may be valuable even when nearby cells have many checklists.

### 3.2 Independent-observer density

\[
O_{it}=\left|\{o:o\text{ submitted a checklist in }(i,t)\}\right|.
\]

This distinguishes broad evidence from repeated sampling by one prolific observer.

### 3.3 Ecological–spatiotemporal effective coverage

For candidate \(a=(i,t)\), define:

\[
C(a\mid D)=\sum_{b\in D}
\exp\left[
-\frac{d_{space}(a,b)^2}{2\ell_s^2}
-\frac{d_{time}(a,b)^2}{2\ell_t^2}
-\frac{d_{habitat}(a,b)^2}{2\ell_h^2}
\right].
\]

Large \(C\) means the candidate resembles many existing observations. A bounded redundancy index is:

\[
R(a\mid D)=\frac{C(a\mid D)}{1+C(a\mid D)}.
\]

This is not exact ecological information gain, but it is transparent and inexpensive.

### 3.4 Portfolio redundancy

Let \(k(a,b)\) be similarity between candidates. Define:

\[
P(A)=\sum_{\{a,b\}\subseteq A}k(a,b).
\]

A simple coverage utility is:

\[
U_{coverage}(A)=\sum_{a\in A}q(a)-\lambda P(A),
\]

where \(q(a)\) is a gap, uncertainty, or priority score.

## 4. Retrospective encounter model

For each focal species:

\[
y_{sijt}\sim\operatorname{Bernoulli}(\pi_{sijt}),
\]

\[
\operatorname{logit}(\pi_{sijt})
=f_s(x_{it})+g_s(e_j)+h_s(t)+b_{s,o(j)}.
\]

Terms represent habitat/geography, observation effort, cyclic season, and optional observer effects.

Predictions should standardize observation effort to a defined protocol \(e^*\):

\[
\hat\pi^{*}_{sit}=P(y=1\mid x_{it},e^*,D).
\]

### Candidate model families

Low-compute options:

- generalized additive model;
- logistic mixed model;
- calibrated random forest;
- gradient-boosted trees;
- spatial basis-function logistic regression.

The benchmark should include at least one interpretable smooth model and one flexible tree model.

## 5. Uncertainty estimation

Tree predictions alone are not epistemic uncertainty estimates. Use one or more of:

1. spatial-block bootstrap;
2. year or temporal-block bootstrap;
3. bootstrap model ensemble;
4. approximate Bayesian GAM;
5. conformal calibration;
6. Gaussian-process residual model.

For the MVP, fit \(M\) spatial-temporal bootstrap models. Let \(\hat\pi^{(m)}_{sit}\) be model \(m\)’s prediction:

\[
\bar\pi_{sit}=\frac1M\sum_{m=1}^M\hat\pi^{(m)}_{sit},
\]

\[
V_{sit}=\frac1{M-1}\sum_{m=1}^M
(\hat\pi^{(m)}_{sit}-\bar\pi_{sit})^2.
\]

This measures model disagreement under the bootstrap design, not total ecological uncertainty. Label it precisely.

## 6. Structured occupancy extension

For prospective repeated visits:

\[
z_{sit}\sim\operatorname{Bernoulli}(\psi_{sit}),
\]

\[
y_{sijt}\mid z_{sit}\sim\operatorname{Bernoulli}(z_{sit}p_{sijt}).
\]

With covariates:

\[
\operatorname{logit}(\psi_{sit})=\alpha_s+f_s(x_{it}),
\]

\[
\operatorname{logit}(p_{sijt})=\beta_s+g_s(e_j,o_j,weather_j).
\]

The field design must define a period during which occupancy can reasonably be treated as closed.

## 7. Information objectives

### 7.1 Exact expected information gain

For candidate observation \(a\):

\[
IG(a\mid D)=H(\theta\mid D)-
\mathbb E_{y_a\sim p(y_a\mid D)}
[H(\theta\mid D,y_a)].
\]

Equivalently:

\[
IG(a\mid D)=I(\theta;y_a\mid D).
\]

For a set \(A\):

\[
IG(A\mid D)=I(\theta;y_A\mid D).
\]

Exact refitting for every candidate outcome and route is usually too expensive for the MVP.

### 7.2 Predictive entropy baseline

For Bernoulli probability \(\pi_a\):

\[
H(y_a\mid D)=-\pi_a\log\pi_a-(1-\pi_a)\log(1-\pi_a).
\]

This is largest near 0.5. It is easy to compute but may overvalue irreducible noise and ignores redundancy unless extended to sets.

### 7.3 Ensemble disagreement

For \(M\) predictions:

\[
U_{QBC}(a)=H(\bar\pi_a)-\frac1M\sum_mH(\pi_a^{(m)}).
\]

This query-by-committee score emphasizes model disagreement rather than cases where all models agree that the outcome is intrinsically uncertain.

### 7.4 Integrated variance reduction

Let \(\mathcal G\) be a target grid. Define:

\[
U_{IVR}(A)=\sum_{g\in\mathcal G}w_g
[V_g(D)-\mathbb E_{y_A}V_g(D,y_A)].
\]

This values observations that reduce uncertainty beyond the sampled cell.

### 7.5 Fisher-information approximation

If candidate \(a\) contributes approximate information matrix \(J_a\), a D-optimal criterion is:

\[
U_D(A)=\log\det\left(J_0+\sum_{a\in A}J_a\right)-\log\det(J_0).
\]

This is efficient for generalized linear or locally linearized models and often has diminishing returns.

### 7.6 Gaussian-process mutual information

For latent Gaussian field covariance \(K_A\) and noise variance \(\sigma^2\):

\[
U_{GP}(A)=\frac12\log\det(I+\sigma^{-2}K_A).
\]

This gives a mathematically clean submodular objective, although a full multi-species GP may be more expensive than the baseline.

## 8. Multi-species utility

### 8.1 Weighted additive utility

\[
U(A)=\sum_{s\in\mathcal S}w_sU_s(A).
\]

Possible weights:

- equal species weight;
- equal weight within ecological guild;
- conservation or management priority;
- migration phase;
- uncertainty or decision relevance.

Avoid automatic extreme inverse-prevalence weights for rare species, which can make unstable models dominate.

### 8.2 Capped utility

Prevent one species from dominating:

\[
U(A)=\sum_sw_s\min\{U_s(A),\tau_s\}.
\]

### 8.3 Guild utility

Group species by ecological guild:

\[
U(A)=\sum_gv_gU_g(A).
\]

This may be more stable than optimizing many sparse species independently.

### 8.4 Community latent-factor utility

Represent shared species variation with latent ecological factors \(\eta\) and optimize:

\[
U(A)=I(\eta;y_A\mid D).
\]

This is a Tier 2 extension.

## 9. Scientific value versus decision value

Suppose decision \(d\in\mathcal D\) has utility \(L(d,\theta)\). Expected value of sample information is:

\[
EVSI(A)=
\mathbb E_{y_A}
\left[
\max_d\mathbb E[L(d,\theta)\mid D,y_A]
\right]
-
\max_d\mathbb E[L(d,\theta)\mid D].
\]

Potential decisions include:

- where to establish permanent monitoring sites;
- which habitat strata need structured surveys;
- which migration week needs recruitment;
- whether a candidate restoration area warrants professional assessment.

The MVP can use entropy and disagreement. A later study should compare those objectives with EVSI.

## 10. Observer model

### 10.1 Detection capability

Let \(r_o\) be an observer profile and \(d_s\) species difficulty:

\[
\operatorname{logit}(p_{s,o})=\gamma_{s0}+\gamma_{s1}r_o+\gamma_{s2}d_s+\gamma_{s3}r_od_s.
\]

This allows experience to matter more for cryptic or difficult species.

### 10.2 Broad private profiles

For the prospective MVP, use broad categories:

- beginner;
- intermediate;
- advanced;
- unknown.

Prefer self-report or protocol-specific calibration. Historical observer effects should remain private and research-only.

### 10.3 Observer-conditional information

\[
U(a,o)=\mathbb E_{y\mid a,o,D}[\text{posterior improvement}].
\]

A beginner route can still be valuable when common-species detections and complete non-detections fill an important effort gap.

### 10.4 Participant-learning value

Optionally define:

\[
L(a,o)=\mathbb E[\text{increase in calibrated identification ability}\mid a,o].
\]

Report learning value separately from ecological value.

## 11. Acceptance and completion

Let \(q(o,R)\) be the probability observer \(o\) completes route \(R\). Features may include:

- travel burden;
- route duration and stops;
- accessibility;
- expected species interest;
- novelty;
- weather;
- timing;
- observer experience;
- whether a route menu or a single assignment is offered.

Expected realized utility is:

\[
U_{realized}(R,o)=q(o,R)U_{science}(R,o).
\]

Initially use transparent burden penalties. Estimate completion probabilities only after enough prospective data exist.

## 12. Route optimization

Let \(G=(V,E)\) be a travel graph and \(V_c\subseteq V\) candidate observation sites. Edge cost \(c_{uv}\) is travel time or generalized burden.

A route \(R=(v_0,v_1,\ldots,v_k)\) must satisfy:

\[
\sum_{r=0}^{k-1}c_{v_rv_{r+1}}+\sum_{r=1}^k\tau_{v_r}\le B,
\]

where \(\tau_v\) is observation time and \(B\) is the total budget.

The optimization is:

\[
\max_RU(V(R)\mid D)
\]

subject to start/end, time, public-access, daylight, difficulty, maximum-stop, and sensitive-site constraints.

### 12.1 Multiple volunteers

For routes \(R_1,\ldots,R_m\):

\[
\max U\left(\bigcup_{k=1}^mV(R_k)\mid D\right)
-\lambda\sum_{k\ne h}\operatorname{Overlap}(R_k,R_h).
\]

If the core utility is submodular, redundancy is naturally penalized through diminishing marginal returns.

### 12.2 Observer-route assignment

Let \(x_{or}=1\) when observer \(o\) is assigned route \(r\). Optimize expected realized utility subject to one route per participant, route capacities, profile requirements, and burden constraints.

## 13. Submodularity

A set function is submodular when:

\[
U(A\cup\{x\})-U(A)\ge U(B\cup\{x\})-U(B)
\]

for every \(A\subseteq B\).

Interpretation: adding a site has lower marginal value after more similar sites are already selected.

For a nonnegative monotone submodular utility under a cardinality constraint, greedy selection has a classic \(1-1/e\) approximation guarantee. Route constraints lead to submodular-orienteering variants.

Foundations:

- [Nemhauser and Wolsey 1978](https://doi.org/10.1287/moor.3.3.177)
- [Krause et al. 2008](https://jmlr.org/beta/papers/v9/krause08a.html)

Do not claim the full human-aware objective is submodular without proof. Completion models, fairness constraints, and observer interactions can break monotonicity or submodularity.

## 14. Fairness and accessibility constraints

### Geographic minimum coverage

For geographic groups \(G_g\):

\[
|A\cap G_g|\ge m_g.
\]

### Habitat representation

Require minimum observations across habitat strata.

### Burden equity

Report or constrain burden variation:

\[
\max_oB_o-\min_oB_o\le\delta.
\]

### Accessible-route portfolio

Require a specified fraction of routes to meet accessibility levels. Evaluate the tradeoff as a Pareto frontier rather than assuming it is costless.

## 15. Beginner suitability score

A transparent baseline is:

\[
S_{beginner}(a)=
\sum_sw_sP(s\text{ detectable by beginner at }a)U_s(a)-\lambda D(a),
\]

where \(D(a)\) penalizes difficult identification sets, unsafe access, excessive complexity, or low expected protocol quality.

## 16. Baseline algorithms

Implement in this order:

| Code | Algorithm |
|---|---|
| B0 | random feasible route |
| B1 | hotspot/richness route |
| B2 | least-sampled route |
| B3 | environmental-diversity route |
| B4 | pointwise entropy then routing |
| B5 | greedy marginal utility per added minute |
| B6 | route-aware local search |
| B7 | human-aware expected-realized utility |

Local-search moves:

- insert;
- delete;
- swap;
- 2-opt travel improvement;
- exchange stops across volunteers.

## 17. Recommended MVP utility

Exact expected posterior information is not required initially. Use:

\[
U_{MVP}(A)=
\sum_sw_s
\left[
\sum_{a\in A}q_{sa}-
\lambda_s\sum_{\{a,b\}\subseteq A}k_s(a,b)
\right],
\]

where:

- \(q_{sa}\) combines bootstrap disagreement and gap priority;
- \(k_s(a,b)\) measures similarity in space, week, habitat, and predicted response;
- \(\lambda_s\) controls redundancy.

Advantages:

- transparent;
- fast;
- supports ablation;
- easy to optimize;
- does not pretend to be exact Bayesian information gain.

Compare it with GP mutual information or D-optimal design on smaller instances.

## 18. End-to-end pseudocode

```text
INPUT:
  historical complete checklists D
  target week t
  candidate public sites V
  volunteer profile o
  route budget B

1. Fit or load species models using only data available before t.
2. Predict standardized encounter rates at candidate sites.
3. Estimate uncertainty using spatial-temporal bootstrap models.
4. Calculate per-site multi-species value q(s, v).
5. Calculate sparse pairwise redundancy k(s, v, u).
6. Exclude inaccessible, unsafe, closed, or sensitive sites.
7. Build or load the travel-time matrix.
8. Construct an initial route by marginal utility per added minute.
9. Improve with insert, swap, delete, and 2-opt moves.
10. Calculate scientific utility, expected completion, habitat coverage,
    accessibility, and explanation features.
11. Return a small menu of meaningfully different routes.
12. Log model, utility, candidates, routes offered, and participant choice.
```

## 19. Compute considerations

### Fast components

- checklist aggregation;
- grid counts;
- sparse kernel redundancy;
- tree and GAM prediction;
- greedy route construction;
- local search.

### Likely bottlenecks

- all-pairs site similarity;
- exact refitting for hypothetical outcomes;
- full Bayesian multi-species models;
- all-pairs road travel matrices;
- many bootstrap models across many species.

### Mitigations

- sparse nearest-neighbor graphs;
- approximate nearest neighbors;
- candidate pruning;
- cached predictions;
- low-rank covariance approximations;
- weekly rather than daily models;
- focal-species portfolio;
- parallel species fitting;
- precomputed travel matrices.

## 20. Candidate mathematical deliverables

A technical contribution could include one of:

1. proof that a simplified utility is monotone submodular;
2. approximation guarantee for a simplified volunteer-route problem;
3. a new redundancy kernel validated against posterior information gain;
4. empirical curvature analysis explaining why greedy is near-optimal;
5. regret analysis for observer-aware versus observer-agnostic assignment;
6. a Pareto frontier between scientific value, route burden, and accessibility.

One rigorous contribution plus a careful application is enough; the project does not need all six.
