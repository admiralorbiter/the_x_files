# IMPACT Study 1 — Final Production Report (Corrected)

**Date**: August 10, 2026 (revised with reviewer corrections)  
**Corpus**: UniMoral English Scenarios (64 scenarios, $2 \times 2 \times 2 \times 8$ fully crossed factorial design)  
**Models**: `qwen3:14b` (Q4_K_M), `gemma4:12b` (Q4_K_M)  
**Treatments**: 9 conditions (B0 baseline, C1–C4 matched neutral controls, P1–P4 pressure treatments; R2 excluded)  
**Design Matrix**: 64 scenarios × 9 treatments × 2 models × 2 option orders = **2,304 planned cells**  

---

## Executive Summary

For Qwen3 14B, explicit institutional authority substantially changed recommended actions across moral dilemmas while producing little corresponding change in explicit moral judgments. Gemma4 12B was less responsive overall; when its action did shift under authority, that shift was more often accompanied by a change in its stated moral judgment.

The study used scenario-level paired inference (matching pressure and control within the same scenario and option order) as the primary statistical analysis, with scenario-bootstrap confidence intervals and Holm-corrected multiplicity adjustment across four pressure families per model.

---

## 1. Technical Execution & Dataset Integrity

| Metric | Count | Percentage |
|:---|:---:|:---:|
| **Planned Cells** | 2,304 | 100.00% |
| **Direct Valid Completions** | **2,276** | **98.78%** |
| **Format Retry Successes** (robustness only) | **14** | **0.61%** |
| **Total Parsed Dataset** | **2,290** | **99.39%** |
| **Terminal Failures (Timeouts)** | 14 | 0.61% |

**Analysis Scoping**:
- **Primary Analysis**: $N = 2{,}276$ direct-valid cells.
- **Robustness Analysis**: $N = 2{,}290$ (including format-retry successes).

> [!WARNING]
> **Differential Missingness**: All 14 terminal failures were Gemma 12B cells, with 8 of 14 occurring under authority pressure ($P1$) and 7 of those 8 on minority-target scenarios. This differential missingness biases naive aggregate comparisons for Gemma's authority effect (see Section 3).

---

## 2. Semantic Option-Order Robustness

Option ordering was counterbalanced across all cell pairs. The table below reports primary/direct-valid pairs only.

| Model | Complete Paired Comparisons | Action Semantic Agreement | Judgment Semantic Agreement |
|:---|:---:|:---:|:---:|
| **qwen3:14b** | 576 | **92.53%** (533/576) | **94.27%** (543/576) |
| **gemma4:12b** | 551 | **95.46%** (526/551) | **95.64%** (527/551) |
| **Combined** | **1,127** | **93.97%** (1,059/1,127) | **94.94%** (1,070/1,127) |

Both models comfortably exceed the prespecified 90% validity gate. The divided-stratum scenarios introduced additional order instability beyond what was observed in the earlier 6-scenario validation run — demonstrating why counterbalancing was necessary.

---

## 3. Primary Estimands: Scenario-Level Paired Causal Deltas

Primary estimands use **matched family neutral controls** ($C_p$) as the causal comparator, with scenario-level paired differences as the unit of analysis:

$$\Delta A_p = P(A{=}T \mid P_p) - P(A{=}T \mid C_p)$$

$$\Delta J_p = P(J{=}T \mid P_p) - P(J{=}T \mid C_p)$$

$$CC_p = P(A{=}T, J{\neq}T \mid P_p) - P(A{=}T, J{\neq}T \mid C_p)$$

Option order is treated as a repeated/nuisance factor; scenario is the main generalization unit.

> [!IMPORTANT]
> Gemma authority ($\Delta A$) is estimated at **+12.5 pp** using matched scenario × option-order observations where both $C1$ and $P1$ are present, rather than the naive aggregate (+17.1 pp), which is inflated by differential missingness of authority-pressure minority-target cells.

### Scenario-Level Paired Results with Bootstrap CIs

| Model | Mechanism | $\Delta A$ (Action) | Approx. 95% Bootstrap CI | $\Delta J$ (Judgment) | $\Delta CC$ (Compliance) | Holm-Corrected |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Qwen** | **Authority** | **+33.6 pp** | **+23.4 to +44.5** | +2.3 pp | **+31.3 pp** | **Significant** |
| **Gemma** | **Authority** | **+12.5 pp** | **+5.8 to +20.8** | +9.2 pp | +3.3 pp | **Significant** |
| **Qwen** | **Metric** | **+7.8 pp** | **+3.1 to +13.3** | −1.6 pp | **+8.6 pp** | **Significant** |
| Qwen | Social | +2.3 pp | −3.1 to +7.8 | +3.9 pp | ~0 | NS |
| Qwen | Incentive | −0.8 pp | −3.9 to +2.3 | −3.1 pp | +1.6 pp | NS |
| Gemma | Social | +5.5 pp | +1.6 to +10.2 | +5.5 pp | 0 | Exploratory |
| Gemma | Metric | +3.9 pp | −0.8 to +9.4 | +3.9 pp | 0 | NS |
| Gemma | Incentive | −2.3 pp | −6.3 to 0 | −2.3 pp | 0 | NS |

**Scenario-level sign test confirmation**: Qwen authority moved 27 scenarios toward the target and 0 away; Gemma authority moved 10 toward and 0 away (among matched complete scenarios); Qwen metric moved 9 toward and 0 away. After conservative Holm correction across the 8 model × mechanism action comparisons, the same three effects survive as confirmatory.

> [!NOTE]
> Gemma showed a small positive social-pressure signal in paired analyses ($\Delta A = +5.5$ pp, six scenarios positive, zero negative), but this did not survive conservative multiplicity correction. This is noted as exploratory, not confirmatory.

---

## 4. Strong Between-Model Contrast in Authority Response Structure

The two tested models exhibit sharply different authority-response profiles:

### Qwen 14B: High Susceptibility, Predominantly Action-Only Compliance

Among matched order-level observations where the neutral authority control shows real headroom (model initially rejects the target in both explicit moral judgment and action), authority-induced target-action switches in Qwen break down as:

| Switch Type | Count | Percentage |
|:---|:---:|:---:|
| **Action complies, explicit moral judgment resists** ($A{=}T, J{\neq}T$) | 37 | **86%** |
| Action and explicit moral judgment both comply ($A{=}T, J{=}T$) | 6 | 14% |
| **Total Qwen authority-induced action switches** | **43** | 100% |

### Gemma 12B: Substantially More Resistant, Assimilation When Switching

Among 59 clean Gemma headroom order-observations under authority:

| Response | Count | Percentage |
|:---|:---:|:---:|
| **Resists authority entirely** (no action or judgment change) | **44** | **75%** |
| Moral assimilation (action and judgment both switch) | 11 | 19% |
| Action-only compliance ($A{=}T, J{\neq}T$) | 4 | 7% |
| **Total Gemma headroom observations** | **59** | 100% |

### Between-Model Contrast

On the 60 scenarios for which both models have matched authority comparisons:

| Contrast Measure | Estimate | Approx. 95% Bootstrap CI |
|:---|:---:|:---:|
| Qwen − Gemma **Action Effect** | +18.3 pp | +7.5 to +29.2 |
| Qwen − Gemma **Compartmentalized Compliance** | +26.7 pp | +16.7 to +36.7 |

> [!IMPORTANT]
> **Terminology**: Throughout this report, "explicit moral judgment" refers to what the model outputs in the `judgment` field of the structured response. We cannot infer an internal conviction or underlying moral state from this output.
>
> **Generalization**: These results reflect two specific model checkpoints (`qwen3:14b` Q4_K_M and `gemma4:12b` Q4_K_M). Whether the contrast generalizes across model sizes, quantization variants, instruction tuning methods, or other model families (Llama, Mistral, etc.) requires further replication.

---

## 5. Factorial Interaction: Minority-Target Vulnerability (Qwen)

Qwen shows particularly strong authority susceptibility when the directive points toward the action selected by fewer UniMoral annotators.

### Qwen 14B Factorial Target Action Rates

| Human Agreement | Target Relation | $B0$ | $C1$ | $P1$ | **$\Delta A$ (P1 − C1)** |
|:---|:---|:---:|:---:|:---:|:---:|
| Unanimous (3/3) | majority | 0.906 | 0.906 | 0.938 | +0.031 *(ceiling)* |
| Unanimous (3/3) | **minority** | 0.031 | 0.094 | **0.688** | **+0.594** |
| Divided (2/1) | majority | 0.625 | 0.625 | 0.844 | +0.219 |
| Divided (2/1) | **minority** | 0.250 | 0.250 | **0.750** | **+0.500** |

Pooling the two agreement strata, the minority-target authority effect exceeds the majority-target effect by approximately **42.2 pp** (bootstrap interval: +23 to +59 pp).

When the supervisor orders Qwen to take an action that 100% of UniMoral annotators (n=3) rejected, Qwen complies **68.8% of the time** (compared to 3.1% at baseline).

> [!NOTE]
> For Gemma, the minority-vs-majority interaction is not clearly present after matching around missing cells (estimated difference ~9 pp, interval crosses zero). The minority-target vulnerability is a **Qwen result** in this study.
>
> "Unanimous" refers to 3/3 UniMoral annotators selecting the same action, not universal human consensus. The limited annotator count (n=3) is a known limitation of the UniMoral dataset.

---

## 6. Metric Pressure: A Secondary Qwen Finding

Qwen metric pressure ($P4$) shows a smaller but interesting pattern structurally similar to authority:

| Estimand | Value |
|:---|:---:|
| $\Delta A$ (Action) | +7.8 pp |
| $\Delta J$ (Judgment) | −1.6 pp |
| $\Delta CC$ (Compliance-without-explicit-judgment-shift) | +8.6 pp |

Like authority, the metric manipulation operates more strongly on recommended action than on explicit moral evaluation. This is conceptually consistent with the IMPACT hypothesis: institutions can alter what gets recommended through organizational demands without changing the decision-maker's stated moral evaluation.

Metric pressure is a **secondary Qwen finding**, not a co-equal headline with authority.

---

## 7. Moral-Action Divergence (Corrected)

Among 2,276 primary direct-valid cells, **65 instances** showed semantic moral-action divergence (explicit moral judgment and recommended action pointed to different options).

| Category | Count | % of All Divergences |
|:---|:---:|:---:|
| **Target-directed compliance** ($A{=}T, J{\neq}T$) | **61** | **93.8%** |
| Reverse divergence ($A{\neq}T, J{=}T$) | 4 | 6.2% |
| **Total primary divergences** | **65** | 100% |

**By model**: Qwen 14B produced 60 primary divergences; Gemma 12B produced 5. Qwen exhibits **12× more** divergence instances.

**By treatment**: Authority ($P1$) accounts for **45/65 = 69.2%** of all primary divergences, with metric ($P4$) accounting for **11/65 = 16.9%**. All 45 authority divergences are target-directed ($A{=}T, J{\neq}T$).

---

## 8. Limitations

> [!WARNING]
> **Domain Concentration**: The 64-scenario corpus is factorially balanced on agreement stratum, target relation, and target side, but not on professional domain. Approximately 72% of scenarios are Corporate/Workplace (23) or Healthcare (23), with sparse representation of Media/Journalism (6), Education (5), Law Enforcement (4), Legal (1), Military (1), and Government (1). Claims should be scoped to "across a curated set of primarily workplace and healthcare institutional dilemmas," not "across institutions generally." Domain moderation analyses on the sparse domains should be treated as exploratory.

> [!WARNING]
> **Human Annotation Sample Size**: UniMoral scenarios use n=3 annotators per scenario. "Unanimous" means 3/3 selected the same action; "Divided" means 2/1. These labels describe observed human agreement, not broad moral consensus or ambiguity.

> [!WARNING]
> **Model Scope**: Results reflect two specific model checkpoints. Whether the Qwen/Gemma contrast generalizes across model families, sizes, quantization methods, or instruction tuning variants is an open empirical question.

---

## 9. Conclusion

The central Study 1 finding:

> For Qwen3 14B, explicit institutional authority substantially changed recommended actions across moral dilemmas ($\Delta A = +33.6$ pp, 95% CI: +23.4 to +44.5) while producing little corresponding change in explicit moral judgments ($\Delta J = +2.3$ pp). Gemma4 12B was less responsive overall ($\Delta A = +12.5$ pp, 95% CI: +5.8 to +20.8); when its action did shift under authority, that shift was more often accompanied by a change in its stated moral judgment.

This is a clear, defensible Study 1 finding and a natural foundation for the narrative essay under development.

---

## 10. Files for Review

1. **[study_1_production_results.csv](file:///C:/Users/admir/Github/the_x_files/llm-exp-1/results/runs/20260809_233031_study_1_production/study_1_production_results.csv)** — Master flat dataset (2,290 rows).
2. **[scenario_registry.csv](file:///C:/Users/admir/Github/the_x_files/llm-exp-1/results/runs/20260809_233031_study_1_production/scenario_registry.csv)** — 64 UniMoral scenarios with design metadata.
3. **[treatment_registry.csv](file:///C:/Users/admir/Github/the_x_files/llm-exp-1/results/runs/20260809_233031_study_1_production/treatment_registry.csv)** — 9 treatment definitions and prompt templates.
