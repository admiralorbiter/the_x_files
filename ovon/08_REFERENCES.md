# Annotated References and Data Sources

**Last reviewed:** 2026-08-05

This is a focused starting bibliography, not a completed systematic review.

## A. eBird data and analytical guidance

### eBird. Download eBird Data Products

https://science.ebird.org/en/use-ebird-data/download-ebird-data-products

Official description of the eBird Basic Dataset, Sampling Event Data, Status and Trends products, eBird Observational Dataset, and public API. The EBD is updated monthly and custom requests can include associated sampling-event data.

### Strimas-Mackey et al. Best Practices for Using eBird Data, Version 2.0

https://ebird.github.io/ebird-best-practices/

Practical guide covering EBD/SED processing, complete checklists, shared-checklist collapse, zero filling, effort filtering, spatiotemporal subsampling, encounter-rate modeling, relative abundance, calibration, and prediction.

### Johnston et al. 2021. Analytical guidelines to increase the value of community science data

https://doi.org/10.1111/ddi.13271

Shows that reliable inference improves substantially when analyses use complete checklists, effort covariates, spatial subsampling, and suitable models. This is the main methodological foundation for the retrospective pipeline.

### eBird data privacy and data use

https://support.ebird.org/en/support/solutions/articles/48001078113

Official summary of noncommercial use, request-purpose restrictions, non-transfer and non-redistribution rules, citations, derived products, and commercial permission.

### eBird Status and Trends terms

https://science.ebird.org/en/status-and-trends/products-access-terms-of-use

Important restrictions for redistribution and use in web-based decision-support tools. Review before any public application.

## B. Detection and occupancy

### MacKenzie et al. 2002. Estimating site occupancy rates when detection probabilities are less than one

https://pubs.usgs.gov/publication/5224176

Foundational occupancy framework separating latent site occupancy from imperfect detection. Supports reserving occupancy claims for repeat-visit designs.

### Ahmed et al. 2025. Spatial Clustering of Citizen Science Data Improves Downstream Species Distribution Models

https://doi.org/10.1609/aaai.v39i27.34993

Examines how citizen-science records can be grouped into sites for occupancy modeling. Relevant to retrospective site construction and its assumptions.

## C. Adaptive citizen-science sampling

### Mondain-Monval et al. 2024. Adaptive sampling by citizen scientists improves species distribution model performance: A simulation study

https://doi.org/10.1111/2041-210X.14355

Direct evidence that directing a portion of volunteer effort toward informative locations can improve species-distribution models in simulation. Establishes that OVON must contribute more than the generic adaptive-sampling premise.

### Experimental evidence that behavioral nudges in citizen science projects can improve biodiversity data

https://academic.oup.com/bioscience/article/73/4/302/7130018

FrogID field evidence that dynamic priority maps can shift participant sampling toward target cells.

### Hanson et al. 2023. Optimizing ecological surveys for conservation

https://doi.org/10.1111/1365-2664.14309

Develops a value-of-information framework connecting survey design to conservation decisions and costs. Important warning that maximum entropy reduction is not automatically maximum management value.

### Williams et al. Monitoring dynamic spatio-temporal ecological processes optimally

https://arxiv.org/abs/1707.03047

Connects dynamic ecological process models, uncertainty, and survey design. Relevant to migration and changing distributions.

## D. Observer effects and participant behavior

### Yu, Wong, and Kelling 2014. Clustering Species Accumulation Curves to Identify Skill Levels of Citizen Scientists

https://doi.org/10.1609/aaai.v28i2.19022

Uses species-accumulation curves to infer observer skill groupings in eBird.

### Kelling et al. 2015. Can Observation Skills of Citizen Scientists Be Estimated Using Species Accumulation Curves?

https://doi.org/10.1371/journal.pone.0139600

Develops a standardized species-accumulation index and examines observer differences and learning.

### Crowley et al. 2026. Modeling intra-observer variation in species detections reveals diverse patterns of change over time in participatory scientists

https://doi.org/10.1093/ornithapp/duag028

Recent method recognizing that individual detection patterns can change nonlinearly over time. Important for longitudinal models and policy-feedback correction.

### Citizen science participant motivations and behaviour: Implications for biodiversity data coverage

https://www.sciencedirect.com/science/article/pii/S0006320723001805

Examines motivations, retention, incentives, and implications for data coverage. Supports testing participant behavior rather than assuming gamification works universally.

### Using discrete choice experiments to explore how site attributes drive birders’ preferences and willingness to travel

https://doi.org/10.1007/s10018-021-00314-w

Shows that birding-site choice reflects rarity, expected diversity, site attributes, travel distance, and heterogeneous participant preferences.

## E. Trends and changing observation processes

### Fink 2023. A Double machine learning trend model for citizen science data

https://doi.org/10.1111/2041-210X.14186

Addresses temporal confounding in citizen-science trend estimation. Relevant because adaptive recommendations alter where and how observations are collected.

### BirdFlow: Learning seasonal bird movements from eBird data

https://doi.org/10.1111/2041-210X.14052

Uses weekly eBird abundance products to model seasonal movement. Useful context for migration-aware objectives, though not required for the MVP.

## F. Information theory, submodularity, and routing

### Krause, Singh, and Guestrin 2008. Near-Optimal Sensor Placements in Gaussian Processes

https://jmlr.org/beta/papers/v9/krause08a.html

Shows that Gaussian-process mutual information can be submodular and develops efficient near-optimal sensor selection.

### Nemhauser and Wolsey 1978. Best Algorithms for Approximating the Maximum of a Submodular Set Function

https://doi.org/10.1287/moor.3.3.177

Classic approximation results for greedy maximization of nondecreasing submodular utility under a cardinality constraint.

### Informative path planning as a maximum traveling salesman problem with submodular rewards

https://doi.org/10.1016/j.dam.2015.01.004

Combines travel/path costs with submodular information rewards. Direct mathematical precedent for route-level sampling.

### Bottarelli et al. 2019. Orienteering-based informative path planning for environmental monitoring

https://doi.org/10.1016/j.engappai.2018.09.015

Frames environmental information collection as an orienteering problem and develops computationally practical heuristics.

### Ott, Kochenderfer, and Boyd 2024. Approximate Sequential Optimization for Informative Path Planning

https://arxiv.org/abs/2402.08841

A scalable informative-path-planning method relevant to later large route instances.

## G. Environmental and access data

### USGS Annual NLCD

https://www.usgs.gov/centers/eros/science/annual-nlcd-data-access

Annual land-cover and land-change data for habitat covariates.

### USGS PAD-US

https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-download

National protected-area and public-access inventory for initial site screening.

### Daymet

https://daymet.ornl.gov/

Daily gridded North American surface weather for detectability, seasonal context, and field conditions.

### OpenStreetMap copyright and license

https://www.openstreetmap.org/copyright

Official ODbL and attribution information for route-network data.

## H. Systematic-review searches still needed

Search combinations of:

- multi-species adaptive ecological survey design;
- human-in-the-loop informative path planning;
- acceptance-aware sampling;
- accessible citizen-science route design;
- active learning with skill-dependent sensors;
- policy-aware correction after adaptive sampling;
- targeted eBird sampling experiments;
- route menus and volunteer choice;
- observer-aware submodular optimization;
- conservation value of citizen-science recommendations.

## I. Suggested citation-manager tags

```text
ebird-data
citizen-science-bias
detection
occupancy
adaptive-sampling
value-of-information
observer-effects
volunteer-behavior
submodular-optimization
orienteering
route-planning
spatial-statistics
migration
data-governance
```
