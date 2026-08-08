# District Futures Lab

## 1. Purpose

District Futures Lab is a **district-level historical replay and scenario system** built on the same Emergence Lab engine.

It should ingest approximately ten years of public historical data, repeatedly ask “what would we have believed at this point in time?”, compare those beliefs with what happened next, and then create conditional future scenarios.

The system should be capable of discovering that an external disruption may have occurred **without being given the label COVID, recession, hurricane, policy change, or teacher shortage in advance**.

## 2. Correct framing

This is not:

- a magic district predictor;
- a causal policy evaluator by default;
- an automated superintendent;
- a tool that turns correlations into explanations.

It is:

- a data-integration agent;
- a historical replay laboratory;
- a structural-break detector;
- an evidence-seeking boundary scanner;
- a scenario generator;
- an uncertainty and assumption explorer.

## 3. Unit of analysis

Primary table:

```text
district × school_year
```

Optional secondary dimensions:

```text
district × school_year × student_group
district × school_year × grade_band
district × school_year × subject
```

Begin at the district level as decided in the project discussion. Do not start with individual students.

## 4. Public data source stack

### NCES Common Core of Data (CCD)

Use for district identity, enrollment, universe/directory attributes, and district finance through the F-33 survey.

CCD is the U.S. Department of Education's comprehensive annual national database of public schools and districts. F-33 provides district revenue and expenditure data.

- https://nces.ed.gov/ccd/
- https://nces.ed.gov/ccd/f33agency.asp

### EDFacts / Ed Data Express

Use for federally reported outcomes and indicators such as chronic absenteeism and other ESSA-related measures when available and comparable across years.

- https://www.ed.gov/data/edfacts-initiative
- https://eddataexpress.ed.gov/resources/reports-and-files/chronic-absenteeism-data

### Civil Rights Data Collection (CRDC)

Use for access/opportunity, discipline, staffing, course access, and civil-rights-related district measures. The CRDC is periodic rather than a clean annual panel, so treat availability explicitly.

- https://civilrightsdata.ed.gov/
- https://civilrightsdata.ed.gov/data

### Census SAIPE

Use for annual school-district poverty context. SAIPE provides annual school-district population and poverty estimates and an API covering historical years.

- https://www.census.gov/programs-surveys/saipe/data/datasets.html
- https://www.census.gov/programs-surveys/saipe/data/api.html

### Census ACS and population/context sources

Use for broader demographic, housing, employment, and household context where district geographies and release cadence support valid comparisons. Record margins of error and geography changes.

### Stanford Education Data Archive (SEDA)

Use selectively for harmonized achievement and covariate research where the covered years and measures fit the question. Do not treat old SEDA releases as a complete ten-year current outcome feed.

- https://cepa.stanford.edu/seda2/data-download

### Missouri DESE

For Missouri districts, prioritize Missouri's official district data, accountability, finance, and MCDS resources when machine-readable or reliably downloadable.

- https://dese.mo.gov/school-data
- https://apps.dese.mo.gov/MCDS/
- https://dese.mo.gov/financial-admin-services/school-finance/data-reports-0

### Kansas KSDE Data Central

For Kansas districts, use KSDE Data Central and state reporting for finance, enrollment, staffing, graduation, and performance measures.

- https://datacentral.ksde.gov/
- https://www.ksde.gov/data-and-reporting
- https://ksreportcard.ksde.gov/

## 5. Data adapter contract

Every data source implements:

```python
class DistrictDataAdapter(Protocol):
    source_id: str

    def discover_releases(self, as_of: date) -> list[Release]: ...
    def fetch(self, release: Release) -> list[RawArtifact]: ...
    def normalize(self, artifact: RawArtifact) -> list[DistrictMetric]: ...
    def metric_passports(self) -> list[MetricPassport]: ...
```

Every raw download is frozen with:

- source URL;
- retrieval date;
- publication/release date;
- content hash;
- source version/year;
- adapter version;
- license/usage note;
- parsing warnings.

## 6. Metric Passports

Do not let the agent merge variables because their labels sound similar.

Every metric requires:

```yaml
metric_id: chronic_absence_rate
label: Chronic absenteeism
numerator: students absent >= 10% of enrolled school days
denominator: students in reporting population
unit: proportion
level: district
school_year_semantics: academic_year
source: EDFacts
comparability_notes: ...
suppression_rules: ...
known_breaks: ...
```

Derived rates must retain numerators and denominators when available.

The district system should automatically flag common analytical reversals already identified in prior project work, including rate-count reversals, subgroup/overall reversals, one-year versus multiyear reversals, participation sensitivity, and suppression uncertainty.

## 7. Historical replay

Historical replay is the key research design.

For each replay origin \(t\):

1. expose only data released by \(t\);
2. build features from that information;
3. fit baseline models;
4. generate forecasts/scenarios for \(t+1, t+2, ...\);
5. advance the replay clock;
6. score against observations when they become available;
7. let the system detect new residual/anomaly patterns;
8. permit boundary scanning using only sources available by that new simulated date.

### No hindsight leakage

If the replay date is March 2019, a 2020 article is unavailable.

If the replay advances to April 2020, newly published evidence about a pandemic may become available and the system can update.

This creates two different abilities worth measuring:

- **forecasting before a shock** — generally impossible to get exactly right;
- **adaptive recognition after onset** — the system should notice that its previous model no longer fits and learn quickly.

## 8. Baseline models

The LLM should not be the numerical forecaster in V1.

Start with transparent baselines:

1. last value;
2. recent linear trend;
3. exponentially weighted trend;
4. ridge regression with lagged district/context variables;
5. robust regression;
6. optional simple Bayesian/dynamic regression later.

For each outcome, report whether a complicated model actually beats the naïve baselines.

## 9. Autonomous shock discovery

This is a general organizational capability, not a COVID exception.

### Phase 1 — detect discontinuity

Signals may include:

- residual magnitude;
- residual clustering across multiple metrics;
- Bayesian change-point probability;
- sudden covariance changes;
- missingness changes;
- synchronized breaks across nearby districts.

Create a `shock_candidate` without explaining it.

### Phase 2 — characterize the footprint

Ask deterministic questions:

- Which metrics moved?
- Which districts moved?
- Did the break occur simultaneously?
- Is the change in level, slope, variance, or missingness?
- Does it affect outcomes, inputs, or both?

### Phase 3 — boundary-scanner investigation

Spawn one or more research agents with queries derived from the footprint:

```text
Kansas City school districts March–June 2020 attendance closure policy
Missouri education emergency order March 2020
Kansas unemployment April 2020
federal school emergency funding 2020
```

The agent is not asked “find COVID.” It is asked “find dated external events capable of producing this observed footprint.”

### Phase 4 — evidence object

A candidate event needs:

- title/description;
- event date range;
- publication date;
- geography;
- affected mechanisms;
- sources;
- confidence as evidence quality, not causal certainty.

### Phase 5 — test explanatory value

Encode a candidate shock using a predeclared family of transformations such as:

- pulse;
- step;
- ramp;
- temporary level change;
- interaction with district vulnerability.

Then test in nested/rolling backtests.

A plausible story that does not improve calibration remains a narrative hypothesis.

## 10. External shock source adapters

The shock scanner should support multiple independent channels.

### Upstream GDELT

Useful for broad historical news/event discovery. Treat it as a discovery source, then preserve article/source evidence.

https://www.gdeltproject.org/data.html

### OpenFEMA

Official federal disaster declarations can provide location and date-bounded natural-disaster shocks.

https://www.fema.gov/about/openfema/disaster-declarations-summaries

### BLS

Local labor-market and employment data can identify economic pressure without relying on news narratives.

https://www.bls.gov/developers/

### Census

Population, poverty, migration/housing context can identify slower external pressure.

### State/federal education policy sources

State education agencies and legislatures can provide dated policy changes, funding rules, and accountability changes.

The architecture should support a discovery adapter and a verification adapter separately.

## 11. Boundary scanning beyond shocks

Not every important external change is abrupt.

Scan for:

- demographic drift;
- enrollment migration;
- housing-cost pressure;
- labor-market changes;
- educator labor supply;
- fiscal changes;
- policy changes;
- transportation changes;
- district boundary changes;
- new program opportunities;
- data-definition changes.

The scanner should maintain “fragile assumptions” such as:

> “Enrollment decline has been approximately linear for four years.”

When evidence invalidates an assumption, create an event and trigger replanning.

## 12. Future scenarios

After historical calibration, generate ensembles of conditional paths.

A scenario is:

```yaml
scenario_id: scn_...
as_of: 2026-06-30
assumptions:
  enrollment: baseline decline
  poverty: stable
  state_funding: current_formula
  chronic_absence_recovery: slow
shocks:
  - type: economic_downturn
    probability_bucket: exploratory
policy_choices:
  - tutoring_expansion
outputs:
  - graduation_rate
  - attendance
  - per_pupil_spending
```

Do not collapse this to “the district will have a 91.3% graduation rate in 2034.”

Prefer bands, scenario families, and sensitivity.

## 13. Evaluation

Primary measures:

- MAE / RMSE against naïve baselines;
- baseline-relative skill;
- interval coverage and width;
- direction accuracy when useful;
- shock detection delay;
- false shock rate;
- external-evidence precision;
- shock-model backtest uplift;
- number of hindsight violations (must be zero);
- data completeness and provenance coverage;
- stability to leaving one data source out.

## 14. COVID as a diagnostic, not a special case

A strong test is whether the replay autonomously behaves roughly like this:

```text
2018–2019: ordinary model fits reasonably
early 2020: residuals/missingness/attendance patterns break
system: flags structural discontinuity
boundary scanner: searches dated external evidence
system: discovers broad health/policy/economic events consistent with footprint
shock object: created with evidence
model: adapts after onset
later replay: scores adaptation speed and uncertainty calibration
```

If the system only works because `covid = 1` was manually inserted, it has not solved the organizational problem we care about.

## 15. Ethical boundary

Public district aggregates can still be misinterpreted.

The product should always distinguish:

- observation;
- correlation;
- structural break;
- external event evidence;
- hypothesized mechanism;
- causal estimate.

Only the last category supports a causal claim, and it requires an appropriate causal research design beyond the default simulator.
