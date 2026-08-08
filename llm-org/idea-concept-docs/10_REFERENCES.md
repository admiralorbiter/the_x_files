# References and Knowledge-Base Seed

This bibliography is intentionally practical. It is a starting canon for the project, not a claim that every source should become an agent prompt.

## A. Existing internal project foundations

The following prior documents supplied important architectural conventions for Emergence Lab:

- `BIG_BRAIN_TIME_SYSTEM_BLUEPRINT.md` — local-first modular architecture, external state, provenance, permission boundaries, retrieval and memory principles.
- `ARCHITECTURE_DECISION_RECORDS.md` — causal event schemas, immutable artifacts, append-only claims, supersession, review boundaries.
- `BIG_BRAIN_TIME_DESIGN_STUDIO.md` — domain kernel, ports/adapters, explicit authority and trust planes, model outputs as proposals.
- `handbook.md` — metric integrity, numerator/denominator discipline, time and paradox/reversal checks in school/organizational analysis.
- `disagreement_aware_stem_feedback_master_plan.md` — local Ollama reproducibility requirements, Flask/SQLite architecture, bounded retries and raw-output retention.

These are design precedents, not direct dependencies.

## B. Organizational learning and coordination

### March — exploration/exploitation

James G. March. “Exploration and Exploitation in Organizational Learning.” *Organization Science* 2(1), 1991.  
https://pubsonline.informs.org/doi/10.1287/orsc.2.1.71

Use for: exploration budgets, organizational learning tradeoffs, path dependence.

### Weick, Sutcliffe, Obstfeld — sensemaking

“Organizing and the Process of Sensemaking.” *Organization Science*, 2005.  
https://pubsonline.informs.org/doi/10.1287/orsc.1050.0133

Use for: ambiguous shocks, competing interpretations, environment scanning.

### Malone & Crowston — coordination theory

“The Interdisciplinary Study of Coordination.” *ACM Computing Surveys*, 1994.  
https://crowston.syr.edu/sites/default/files/acmcs94.pdf

Use for: dependency graphs, coordination cost, blocking and shared resources.

### Wegner — transactive memory

“Transactive Memory: A Contemporary Analysis of the Group Mind.”  
https://dtg.sites.fas.harvard.edu/DANWEGNER/pub/Wegner%20Transactive%20Memory.pdf

Use for: capability registry, “who knows what,” help routing.

### Cohen, March, Olsen — garbage-can model

“A Garbage Can Model of Organizational Choice,” 1972.  
https://iiif.library.cmu.edu/file/Simon_box00030_fld02270_bdl0001_doc0001/Simon_box00030_fld02270_bdl0001_doc0001.pdf

Use for: loose coupling among problems, solutions, participants, and decision opportunities.

## C. Agent and social simulation research

### Generative Agents

Joon Sung Park et al. “Generative Agents: Interactive Simulacra of Human Behavior,” 2023.  
https://arxiv.org/abs/2304.03442

Use for: memory/reflection/planning baseline and emergent social behavior.

### Generative Agent-Based Modeling

Navid Ghaffarzadegan et al., 2023.  
https://arxiv.org/abs/2309.11456

Use for: coupling mechanistic simulation with generative reasoning.

### AgentSociety

Jinghua Piao et al., 2025.  
https://arxiv.org/abs/2502.08691

Use for: large-scale LLM social simulation and external-shock experiments.

### LongHorizon-Harness

Ziyu Ma et al., 2026.  
https://arxiv.org/abs/2608.01964

Use for: explicit external task state, fresh-context execution, audit.

### Harness-Bench

Yilun Yao et al., 2026.  
https://arxiv.org/abs/2605.27922

Use for: harness as an experimental variable.

### OneDayAgent

Jingsheng Zheng et al., 2026.  
https://arxiv.org/abs/2608.05013

Use for: bounded decomposition, memory, verification and repair.

### SearchSwarm

Pu Ning et al., 2026.  
https://arxiv.org/abs/2606.09730

Use for: delegation intelligence and sub-agent return contracts.

### OrgAgent

Yiru Wang et al., 2026.  
https://arxiv.org/abs/2604.01020

Use for: organization structure as a multi-agent design variable.

## D. Change detection and uncertainty

### Bayesian Online Changepoint Detection

Ryan Prescott Adams and David J. C. MacKay.  
https://arxiv.org/abs/0710.3742

Use for: probability of structural breaks and online adaptation.

## E. Local-model/runtime documentation

### Ollama structured outputs

https://docs.ollama.com/capabilities/structured-outputs

Use for: proposal schemas and structured agent contracts.

### Flask application factories

https://flask.palletsprojects.com/en/stable/patterns/appfactories/

### Flask blueprints

https://flask.palletsprojects.com/en/stable/blueprints/

### Flask streaming

https://flask.palletsprojects.com/en/stable/patterns/streaming/

### HTMX SSE

https://htmx.org/extensions/sse/

### Alpine state

https://alpinejs.dev/essentials/state

## F. District education data

### NCES Common Core of Data

https://nces.ed.gov/ccd/

Primary uses: district identity, enrollment/universe data, school/district directory.

### NCES F-33 district finance

https://nces.ed.gov/ccd/f33agency.asp

Primary uses: revenue, expenditure, debt, enrollment-linked finance.

### EDFacts

https://www.ed.gov/data/edfacts-initiative

Primary uses: federally reported education indicators.

### Ed Data Express chronic absenteeism files

https://eddataexpress.ed.gov/resources/reports-and-files/chronic-absenteeism-data

### Civil Rights Data Collection

https://civilrightsdata.ed.gov/

Data downloads:  
https://civilrightsdata.ed.gov/data

### Census SAIPE

https://www.census.gov/programs-surveys/saipe/data/datasets.html

API:  
https://www.census.gov/programs-surveys/saipe/data/api.html

Primary uses: annual district population and school-age poverty context.

### Stanford Education Data Archive

https://cepa.stanford.edu/seda2/data-download

Primary uses: harmonized historical district achievement/covariate research within covered years.

### Missouri DESE school data

https://dese.mo.gov/school-data

Missouri Comprehensive Data System:  
https://apps.dese.mo.gov/MCDS/

School finance reports:  
https://dese.mo.gov/financial-admin-services/school-finance/data-reports-0

### Kansas KSDE

Data Central:  
https://datacentral.ksde.gov/

Data & Reporting:  
https://www.ksde.gov/data-and-reporting

Kansas Report Card:  
https://ksreportcard.ksde.gov/

## G. External pressure / shock discovery sources

### GDELT Project

https://www.gdeltproject.org/data.html

Use as a broad historical event/news discovery layer. Preserve underlying source provenance and do not treat event extraction as unquestionable truth.

### OpenFEMA Disaster Declarations

https://www.fema.gov/about/openfema/disaster-declarations-summaries

Use for official disaster dates/geography.

### Bureau of Labor Statistics public data

https://www.bls.gov/developers/

Use for labor-market shocks and contextual time series.

## H. Reading order for the first week

If only a few papers are read before building, use this order:

1. March — exploration/exploitation.
2. Generative Agents.
3. LongHorizon-Harness.
4. SearchSwarm.
5. Adams & MacKay — change points.
6. Malone & Crowston — coordination.
7. Wegner — transactive memory.
8. AgentSociety.

The goal is not to copy these architectures. It is to understand the design space well enough to recognize when Emergence Lab is doing something genuinely different.
