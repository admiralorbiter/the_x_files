# Research Landscape and Candidate Research Gap

## 1. Why eBird can support rigorous research

eBird is organized around checklists rather than isolated sightings. A checklist represents an observation event and can include date, time, location, protocol, duration, distance traveled, number of observers, species detections, counts, and whether the observer reported all species detected and identified.

That last field is crucial. On a **complete checklist**, an unreported focal species can be treated as a non-detection rather than an unknown omission. Sampling Event Data provide observation-effort metadata that can be used to control part of the observation process. Cornell’s current best-practices guide characterizes eBird as semi-structured: participation is flexible, but the recorded protocol and effort fields support substantially stronger inference than presence-only occurrence records.

Primary methodological sources:

- [eBird Best Practices, Version 2.0](https://ebird.github.io/ebird-best-practices/)
- [eBird Data chapter](https://ebird.github.io/ebird-best-practices/ebird.html)
- [Johnston et al. 2021](https://doi.org/10.1111/ddi.13271)

## 2. Central inferential challenges

### 2.1 Spatial preference bias

Observers are more likely to visit convenient, accessible, established, species-rich, or recently newsworthy locations. Raw observation density is therefore a mixture of bird ecology and human choice. A dense cluster of records does not automatically imply a dense bird population.

### 2.2 Temporal preference bias

Observation effort varies with weekends, seasons, migration peaks, time of day, weather, and growth in eBird participation. A temporal gap must be measured relative to expected ecological change and the normal observation process, not simply as the absence of records.

### 2.3 Variable detection

A bird can be present and not detected. Detection depends on species behavior, habitat, time, duration, distance, group size, weather, and observer experience. The occupancy literature emphasizes that non-detection is not equivalent to absence when detection probability is below one.

Foundational source:

- [MacKenzie et al. 2002](https://pubs.usgs.gov/publication/5224176)

### 2.4 Species-reporting bias

Incomplete checklists cannot safely supply non-detections because an observer may omit common or uninteresting species. Core encounter and occupancy analyses should therefore rely on complete checklists.

### 2.5 Shared-checklist pseudoreplication

Members of one birding party can share a checklist. These records should be collapsed to one independent sampling event rather than treated as multiple surveys.

### 2.6 Spatial imprecision

A traveling checklist covers an area, not a single point. Hotspot coordinates may represent a large property. Environmental covariates must be summarized at a spatial scale compatible with protocol and distance traveled.

## 3. Existing ecological-modeling approaches

### 3.1 Encounter-rate models

Encounter rate is the probability that a species is detected on a checklist under a standardized observation protocol. It is not automatically equivalent to true occupancy, but it provides a useful relative ecological response after effort, season, habitat, and observation variables are addressed.

A general retrospective model is:

\[
y_{sijt}\sim\operatorname{Bernoulli}(\pi_{sijt}),
\]

\[
\operatorname{logit}(\pi_{sijt})=f_s(x_{it})+g_s(e_j)+h_s(t)+b_{s,o(j)},
\]

where \(x\) describes habitat and geography, \(e\) describes observation effort, \(h\) captures seasonal variation, and \(b\) optionally captures observer effects.

For OVON, encounter rate is the recommended retrospective target because historical eBird visits generally do not provide a controlled repeat-visit design that identifies true occupancy and detection separately.

### 3.2 Occupancy models

A single-season occupancy model separates latent presence from observation:

\[
z_i\sim\operatorname{Bernoulli}(\psi_i),
\]

\[
y_{ij}\mid z_i\sim\operatorname{Bernoulli}(z_i p_{ij}).
\]

This requires repeated visits during a period when occupancy can reasonably be treated as stable. Opportunistic records can sometimes be grouped into repeated sites, but site construction and closure assumptions are consequential.

Relevant current work:

- [Ahmed et al. 2025, Spatial Clustering of Citizen Science Data](https://doi.org/10.1609/aaai.v39i27.34993)

The prospective OVON pilot can deliberately create fixed sites and repeated visits, enabling a more defensible occupancy extension.

### 3.3 Relative abundance

Relative abundance models the expected count on a standardized checklist rather than an absolute population count. A hurdle model can combine detection probability and conditional count. This is an optional extension because counts are more sensitive to flocking, counting behavior, and unknown “X” values than binary detection.

### 3.4 Trend models

Citizen-science trends can be confounded by changing participation and observer behavior. This becomes especially important once OVON itself starts directing effort. The recommendation policy must be logged so future analyses can distinguish ecological change from policy-driven sampling change.

Relevant source:

- [Fink 2023, Double machine learning trend model](https://doi.org/10.1111/2041-210X.14186)

## 4. Existing adaptive citizen-science sampling

The broad proposition—directing volunteers toward informative places—is not new.

### 4.1 Simulation evidence

Mondain-Monval and colleagues used simulated ecological communities and found that directing a portion of citizen-science effort toward informative locations could improve downstream species-distribution models.

- [Mondain-Monval et al. 2024](https://doi.org/10.1111/2041-210X.14355)

A paper whose only result is “adaptive sampling can outperform unstructured sampling” would therefore be insufficiently differentiated.

### 4.2 Behavioral field evidence

A FrogID experiment used dynamic maps and behavioral nudges to encourage participants to sample priority cells, and participants changed their behavior in the intended direction.

- [BioScience field experiment](https://academic.oup.com/bioscience/article/73/4/302/7130018)

This establishes that targeted requests can influence at least some citizen-science participants. OVON should examine which recommendations are accepted, by whom, at what burden, and with what realized information value.

### 4.3 Remaining integrated questions

Important questions remain under-integrated:

- How should several species be valued simultaneously?
- When are proposed observations redundant?
- How should a connected route be optimized rather than a disconnected set of cells?
- How should participant completion probability change the objective?
- How should assignments differ by observer experience?
- Does predictive entropy reduction improve an actual management decision?
- How should geographic, accessibility, and participant equity be represented?
- What happens when adaptive sampling changes the future training distribution?

These questions define OVON’s opportunity.

## 5. Information gain versus decision value

The motivating expected-information objective is:

\[
IG(l)=H(\Theta\mid D)-\mathbb{E}_{y_l}[H(\Theta\mid D,y_l)].
\]

This is coherent when the ecological target \(\Theta\), observation process, and predictive distribution are specified. However, a high-information observation is not necessarily a high-value conservation observation.

Examples:

- resolving uncertainty about a secure common species can reduce entropy;
- resolving whether a sensitive species occupies a management unit may change an action;
- confirming a famous hotspot may engage volunteers but add little evidence;
- sampling a difficult or unsafe site may be theoretically useful but inappropriate.

Ecological survey design can instead optimize the **expected value of sample information** for a decision:

- [Hanson et al. 2023](https://doi.org/10.1111/1365-2664.14309)

OVON should compare at least two objectives:

1. **map-learning utility:** improve ecological predictions broadly;
2. **decision utility:** improve a specified monitoring or management decision.

Volunteer learning and enjoyment should be measured separately rather than silently equated with scientific value.

## 6. Observer skill and learning

Observer capability is not fixed or uniform. Prior eBird research has used species-accumulation curves to estimate differences in detection and identification ability:

- [Yu, Wong, and Kelling 2014](https://doi.org/10.1609/aaai.v28i2.19022)
- [Kelling et al. 2015](https://doi.org/10.1371/journal.pone.0139600)

Recent work models both between-observer differences and within-observer change over time:

- [Crowley et al. 2026](https://doi.org/10.1093/ornithapp/duag028)

This creates an interesting contribution opportunity. Most information-based sampling treats the observer as a generic sensor. OVON can study expected information conditional on observer profile:

\[
IG(l,o),
\]

not merely location \(l\).

The ethical objective is not to rank or shame volunteers. It is to find scientifically reliable tasks for different experience levels. Beginners may be particularly useful when target species are common and detectable, protocols are short and standardized, repeated non-detections are useful, and routes include appropriate training or paired participation.

## 7. Informative path planning and submodularity

Information-based survey design connects to sensor placement and robotics.

Krause, Singh, and Guestrin showed that mutual-information sensor placement for Gaussian processes can be submodular, which permits near-optimal greedy selection under a cardinality constraint:

- [Krause et al. 2008](https://jmlr.org/beta/papers/v9/krause08a.html)

Route constraints transform site selection into an orienteering-type problem. Relevant precedents include:

- [Informative path planning with submodular rewards](https://doi.org/10.1016/j.dam.2015.01.004)
- [Orienteering-based informative path planning](https://doi.org/10.1016/j.engappai.2018.09.015)

The volunteer setting differs from robotic sensing because observations are imperfect and skill-dependent, people may decline routes, visits take time, access and daylight matter, multiple volunteers can duplicate each other, and recommendations affect future behavior. These differences are not side issues; they are the central research problem.

## 8. Participant preference and route completion

Birders select locations based on more than distance. Research indicates heterogeneous preferences for rarity, diversity, naturalness, access, and travel burden. Citizen-science participants also differ in motivation, and gamification does not motivate everyone equally.

Relevant sources:

- [Birding-site attributes and willingness to travel](https://doi.org/10.1007/s10018-021-00314-w)
- [Citizen-science motivations and biodiversity coverage](https://www.sciencedirect.com/science/article/pii/S0006320723001805)

The theoretically highest-value route contributes nothing when nobody completes it. A human-aware objective should therefore include:

\[
P(\text{completion}\mid o,R)\times
\mathbb{E}[\text{scientific utility}\mid o,R,\text{completed}].
\]

## 9. Precise candidate research gap

> Existing work demonstrates adaptive citizen-science sampling, observer-effect modeling, information-based ecological survey design, and informative route planning. Less developed is an integrated framework that selects **multi-stop volunteer routes** using a **multi-species uncertainty objective**, explicitly models **diminishing returns**, conditions realized value on **observer capability and route completion**, and validates the system through both **historical replay and structured field collection**.

This wording remains provisional until a formal systematic literature review is completed.

## 10. Contribution boundaries

### Defensible early claims

- Some cells, habitats, weeks, or protocols receive highly repetitive effort.
- Different information objectives select measurably different routes.
- Travel and completion constraints change the theoretical optimum.
- A strategy performs better or worse than named baselines in a defined replay benchmark.
- Structured volunteer routes are feasible or infeasible under observed completion rates.
- Beginner-matched protocols can yield useful complete checklists under specified conditions.

### Claims requiring stronger evidence

- A route improves true population estimates.
- A checklist caused a conservation action.
- The algorithm generalizes nationwide.
- Entropy reduction is equivalent to ecological importance.
- Low-observation locations are automatically under-monitored.
- A model-derived observer score is a definitive measure of expertise.

## 11. Novelty test before publication

Conduct a structured search using combinations of:

- adaptive biodiversity sampling;
- citizen-science survey design;
- eBird active learning;
- human-aware informative path planning;
- volunteer route optimization;
- multi-species value of information;
- observer-dependent sampling design;
- submodular ecological monitoring.

Create a comparison matrix:

| Dimension | Closest prior work | OVON target |
|---|---|---|
| Real citizen-science data | Varies | EBD plus prospective pilot |
| Adaptive selection | Often | Yes |
| Connected route constraint | Rarely integrated | Yes |
| Multi-species objective | Sometimes | Yes |
| Observer profile | Usually separate | Yes |
| Completion probability | Rarely ecological | Yes |
| Historical replay | Varies | Yes |
| Prospective field test | Limited | Planned |
| Decision value | Separate literature | Extension |

Advance the publication claim only if at least one central combination remains materially distinct.
