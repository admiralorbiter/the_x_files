# Human-Aware, Route-Constrained Multi-Species Adaptive Sampling for Citizen-Science Bird Surveys: Simulation Study

> **[WARNING / DISCLAIMER]**: All numerical results in this document are illustrative simulation outputs from synthetic/mock checklist datasets. They are not empirical findings and MUST NOT be cited as empirical results until raw EBD/SED parquet extracts are loaded and re-fitted.

**Authors**: OVON Research Group  
**Target Publication**: *Methods in Ecology and Evolution / Ecological Informatics*  
**Pilot Region**: Greater Kansas City Metropolitan Area & Surrounding Rural Reserves  

---

## Executive Summary & Abstract

Adaptive spatial sampling offers a principled approach to reducing observational bias and spatial-temporal uncertainty in citizen-science species distribution models (SDMs). However, standard active learning policies recommend isolated, unconstrained grid cells that are humanly infeasible for volunteers to visit under real-world time budgets and transit constraints. Furthermore, naive pooling of heterogeneous data sources (complete checklists, presence-only records, and opportunistic photos) distorts detection/non-detection likelihoods.

This paper presents the **Optimal Volunteer Observation Network (OVON)**, a unified mathematical and algorithmic framework for multi-species adaptive sampling. OVON integrates:
1. **Source-Aware Data Provenance**: Formal distinction between eBird complete effort-recorded checklists ($y_{sij} \sim \text{Bernoulli}[\text{logit}^{-1}(\eta_s + g_s(e))]$), GBIF presence-only point processes, and photo-verified iNaturalist records.
2. **Standardized Environmental & Geospatial Covariates**: Multi-scale NLCD land cover, NHDPlus hydrology, NWI Cowardin wetland classifications, and USGS PAD-US public access/safety metadata.
3. **Dynamic Phenology & Standardized Feature Kernels**: Cyclic 52-week species phenology weighting ($w_{s,t}$) coupled with z-score standardized Mahalanobis habitat kernel distances.
4. **Joint Route & Duration Optimization**: Closed-loop OSRM pedestrian/driving itinerary construction under a global time budget $B$, combining submodular spatial-temporal information utility with greedy marginal duration allocation $\frac{U(\tau_i + 5) - U(\tau_i)}{5}$.

In a simulated historical replay experiment (training on simulated 2022 complete checklists and evaluating on 2023 held-out test checklists in Greater Kansas City), the **OVON Variable-Duration Policy** achieved enhanced Brier score reduction per volunteer minute compared to traditional species richness (hotspot) sampling or random feasible routes.

---

## 1. Introduction & Research Scope

Citizen science platforms such as eBird, iNaturalist, and GBIF have generated hundreds of millions of biological observations. However, volunteer sampling suffers from severe spatial, temporal, and observer selection biases:
- **Spatial Clustering**: Volunteers disproportionately sample urban parks, accessible road corridors, and well-known birding "hotspots."
- **Temporal Redundancy**: Repeat visits to the same location during peak weekends yield diminishing marginal information returns.
- **Protocol Heterogeneity**: Opportunistic presence-only observations provide no evidence of species absence, whereas complete effort-recorded checklists provide structured detection/non-detection data.

Existing active sampling algorithms (e.g., pointwise entropy or Query-by-Committee disagreement) select optimal points independently. When constrained to real road networks or pedestrian walking paths, these unconstrained selections force long travel legs between disjoint sites, wasting the majority of a volunteer's time budget in transit.

OVON addresses this challenge by jointly optimizing the **sequence of visited candidate sites** and the **stationary observation duration at each site**, subject to strict travel budget constraints $B$, return-to-hub closed loops, and access/safety bounds.

```
       ┌─────────────────────────────────────────────────────────┐
       │                OVON ARCHITECTURE MAP                    │
       └──────────────────────────┬──────────────────────────────┘
                                  │
      ┌───────────────────────────┴───────────────────────────┐
      ▼                                                       ▼
┌──────────────────────────┐             ┌──────────────────────────┐
│  Data Truth & Provenance │             │ Mathematical Optimization│
├──────────────────────────┤             ├──────────────────────────┤
│• eBird Complete (EBD)    │             │• Standardized Mahalanobis│
│• GBIF Presence-Only      │             │  Habitat Kernels         │
│• iNaturalist Photos      │             │• Dynamic Weekly Weights  │
│• NWI Cowardin Wetlands   │             │• Normalized Submodular   │
│• USGS PAD-US Lands       │             │  Information Utility     │
└─────────────┬────────────┘             └─────────────┬────────────┘
              │                                        │
              └───────────────────┬────────────────────┘
                                  ▼
                ┌───────────────────────────────────┐
                │ Closed-Loop OSRM Pedestrian/Drive │
                │ Itinerary & Duration Allocator    │
                └─────────────────┬─────────────────┘
                                  ▼
                ┌───────────────────────────────────┐
                │   Simulated Historical Replay     │
                │   Out-of-Fold Evaluation          │
                └───────────────────────────────────┘
```

---

## 2. Data Provenance & Observation Models

### 2.1 Decoupled Observation Processes
Rather than naively concatenating presence-only and checklist records into a single observation list, OVON enforces decoupled observational roles:

1. **Complete eBird Checklists ($D_{\text{ebird}}$)**:
   Modeled via Bernoulli detection likelihood with effort covariates (duration $\tau_i$, distance $d_i$, protocol $p_i$):
   $$\text{Pr}(Y_{s,i,t} = 1 \mid \eta_s, \tau_i) = \text{logit}^{-1}\Big(\eta_s(x_i, t) + \beta_{s,1} \log(\tau_i) + \beta_{s,2} d_i\Big)$$
   Where complete checklists absent of species $s$ are zero-filled as explicit non-detections.

2. **Opportunistic Presence-Only Data ($D_{\text{gbif}}, D_{\text{inat}}$)**:
   Modeled via inhomogeneous Poisson point process intensity $\lambda_{s,p}(x, t) = \exp(\eta_s(x, t) + b_p(x, t))$, where $b_p(x, t)$ represents platform-specific observer sampling bias.

### 2.2 Standardized Environmental & Spatial Features
Each candidate site $i$ is described by a 4-dimensional environmental covariate vector $h_i = [c_i, p_i, w_i, g_i]^\top$:
- $c_i$: Percent tree canopy cover (USFS 30m)
- $p_i$: Percent impervious built surface (NLCD 30m)
- $w_i$: Distance to nearest NHDPlus waterbody (km) and NWI wetland Cowardin classification (`PEM1A`, `PFO1A`, `R2UBH`)
- $g_i$: Vegetation greenness index / NDVI proxy

Features are standardized via z-score scaling $z_j = \frac{x_j - \mu_j}{\sigma_j}$ fitted dynamically on training data.

### 2.3 Dynamic Weekly Phenology Priors ($w_{s,t}$)
Target species priorities vary across the annual 52-week calendar. Weekly species weights $w_{s,t}$ are computed dynamically:
$$w_{s,t} = \frac{A_{s,t} \cdot \mu_s}{\sum_{r} A_{r,t} \cdot \mu_r}$$
Where $A_{s,t} \in [0, 1]$ is relative seasonal presence from a 3-week cyclic smoothed GAM spline $\text{logit}(\hat{p}_{s,w}) = \alpha_s + f_s^{\text{cyclic}}(w)$, and $\mu_s \in \{3.0, 2.0, 1.0\}$ represents migratory urgency (Neotropical migrant, winter resident, or year-round resident).

---

## 3. Mathematical Framework & Optimization Algorithm

### 3.1 Submodular Normalized Utility Function
The multi-species information utility for a candidate route stop set $A = \{(s_1, \tau_1), \dots, (s_k, \tau_k)\}$ is defined as:
$$U(A) = \frac{I(A)}{I_{\text{max}}} - \lambda \frac{R(A)}{R_{\text{max}}}$$

Where:
- **Pointwise Information Score**:
  $$I(A) = \sum_{a \in A} \left[ \left(\sum_s w_{s,t} \, q(s, a)\right) \cdot M(\tau_a) \cdot \big(1 - R(a \mid D, t)\big) \right]$$
- **Diminishing Duration Efficiency**: $M(\tau) = 1 - e^{-0.12 \tau}$ (evaluated at $\tau \in \{5, 10, 15, 20\}$ min).
- **Spatiotemporal Historical Redundancy**:
  $$R(a \mid D, t) = \frac{\sum_{d \in D} K(a, d, t)}{1 + \sum_{d \in D} K(a, d, t)}$$
- **Standardized Habitat Gaussian Kernel**:
  $$K(a, b, t_1, t_2) = \exp\left( -\frac{d_{\text{space}}^2(a, b)}{2 \sigma_s^2} \right) \exp\left( -\frac{\|z_a - z_b\|_2^2}{2 \sigma_h^2} \right) \exp\left( -\frac{d_{\text{cyclic}}^2(t_1, t_2)}{2 \sigma_t^2} \right)$$
- **Pairwise Route Redundancy Penalty**:
  $$R(A) = \sum_{i < j} K(a_i, a_j, t, t)$$

### 3.2 Greedy Marginal Gain Duration Allocator
Optimization constructs routes by iteratively selecting the single candidate action $a^*$ that maximizes **marginal utility gain per added minute**:
$$\text{marginal\_eff}(a) = \frac{U(A \cup \{a\}) - U(A)}{\Delta \text{Time}(a)}$$

For duration extensions of existing stops, the evaluator computes:
$$\frac{U(\tau_i + 5) - U(\tau_i)}{5}$$
Repeatedly extending only the single stop with the highest marginal value until the total time budget $B$ is reached.

---

## 4. Simulated Historical Replay Experiment

### 4.1 Experimental Protocol
To evaluate OVON under simulated checklist data, we constructed a **Simulated Historical Replay Benchmark**:
1. **Training Set**: 150 complete eBird checklists generated across Greater Kansas City in **Year $t-1$ (2022)**.
2. **Model Training**: A Calibrated Random Forest model with spatial quadrant block CV was trained for *Passerina cyanea* (Indigo Bunting).
3. **Replay Set**: 150 complete checklists generated in **Year $t$ (2023)**, split into candidate selection pool $D_{\text{candidate}}$ and untouched held-out evaluation set $D_{\text{eval}}$.
4. **Policy Execution**: 5 competing policies selected candidate observation itineraries under a strict 90-minute time budget at Week 18.
5. **Model Re-Fitting**: Detections for selected stops were revealed, added to training data, and models were re-fitted and evaluated on untouched $D_{\text{eval}}$, measuring held-out **Brier Score Reduction**, **Log-Loss Improvement**, and **Information Gain per Volunteer Minute**.

---

## 5. Main Findings & Discussion

### 5.1 Key Simulation Insights
1. **Variable Duration Superiority**:
   Allocating extra observation minutes (15–20 min) to high-uncertainty forest sites while spending 5 min at open-water sites yielded higher overall survey efficiency than fixed 10-minute stops.
2. **Low Route Constraint Penalty**:
   Connecting observation sites into feasibility-constrained closed-loop OSRM routes retained most active learning value due to geographic substitute sites along greenway corridors.
3. **Efficiency Gain Over Hotspots**:
   OVON directed volunteers toward under-sampled spatial-temporal gaps rather than redundant historical hotspots.

---

## 6. Project Artifacts & Software Availability

The complete OVON codebase, test suite, and interactive dashboard are open-source and modularly organized:
- **Core Package**: `src/ovon/`
- **CLI Harness**: `python -m ovon.cli run-experiment`
- **Streamlit Web App**: `python -m ovon.cli dashboard`
- **Test Suite**: 55 passing unit tests (`pytest`)
