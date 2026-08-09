# Implementation Architecture

## 1. Engineering goals

The codebase should optimize for:

- reproducibility;
- resumable long-running local inference;
- immutable raw results;
- dataset provenance;
- treatment validation;
- model/config comparability;
- low-cost pilot iteration;
- clean separation between generation and analysis.

Python is sufficient for v1. Rust can be introduced later for high-throughput parsing or analysis if profiling shows a real bottleneck; Ollama inference will likely dominate runtime.

## 2. Proposed repository structure

```text
impact/
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   ├── pilot.yaml
│   ├── baseline.yaml
│   ├── confirmatory.example.yaml
│   └── models/
│       ├── model_a.yaml
│       └── model_b.yaml
├── data/
│   ├── raw/                 # never edited
│   ├── interim/
│   ├── processed/
│   ├── scenarios/
│   └── manifests/
├── docs/
│   └── ... these research docs ...
├── prompts/
│   ├── system/
│   ├── protocols/
│   └── treatments/
├── src/impact/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── schemas.py
│   ├── datasets/
│   │   ├── base.py
│   │   ├── moral_dilemma.py
│   │   ├── scruples.py
│   │   └── ethics.py
│   ├── scenarios/
│   │   ├── builder.py
│   │   ├── treatments.py
│   │   ├── validator.py
│   │   └── renderer.py
│   ├── inference/
│   │   ├── ollama_client.py
│   │   ├── runner.py
│   │   ├── retry.py
│   │   └── parser.py
│   ├── storage/
│   │   ├── jsonl.py
│   │   ├── parquet.py
│   │   └── manifest.py
│   ├── analysis/
│   │   ├── baseline.py
│   │   ├── pressure.py
│   │   ├── selective_update.py
│   │   ├── mixed_models.py
│   │   └── figures.py
│   └── utils/
│       ├── hashing.py
│       ├── seeds.py
│       └── logging.py
├── tests/
│   ├── test_schemas.py
│   ├── test_treatments.py
│   ├── test_renderer.py
│   ├── test_parser.py
│   ├── test_resume.py
│   └── fixtures/
├── notebooks/
│   └── exploratory_only/
├── results/
│   ├── runs/
│   ├── tables/
│   └── figures/
└── scripts/
    ├── fetch_datasets.py
    └── smoke_test.py
```

## 3. Configuration model

All run-defining settings belong in YAML/TOML and are copied into the run manifest.

Example:

```yaml
experiment:
  name: pilot_pressure_screen
  version: "0.1.0"
  seed: 20260808

models:
  - id: model_a
    ollama_name: "<configured locally>"
    temperature: 0.6
    top_p: 0.9
  - id: model_b
    ollama_name: "<configured locally>"
    temperature: 0.6
    top_p: 0.9

sampling:
  scenarios: 60
  replicates: 5
  human_consensus_strata:
    high: 20
    medium: 20
    low: 20

conditions:
  - neutral
  - institutional_neutral
  - authority_i1
  - incentive_i1
  - social_i1
  - metric_i1
  - relevant_update

output:
  raw_format: jsonl
  analysis_format: parquet
```

## 4. Data contracts

Use typed schemas with Pydantic/dataclasses.

### Scenario

Fields:

- scenario_id;
- source dataset/version/id;
- ethical kernel;
- domain;
- role;
- response options;
- human distribution;
- entropy;
- provenance/license metadata.

### Treatment

Fields:

- treatment_id;
- pressure family;
- intensity;
- direction;
- relevance;
- paraphrase ID;
- text;
- reviewer flags;
- hash.

### RenderedPrompt

Fields:

- scenario_id;
- treatment_id;
- protocol version;
- exact system prompt;
- exact user prompt;
- prompt hash;
- option ordering.

### InferenceRecord

Fields:

- run_id;
- model config;
- scenario/treatment/protocol IDs;
- replicate;
- request parameters;
- raw response;
- parsed judgment/action/confidence/rationale;
- parse status;
- refusal flag;
- timing/tokens;
- error/retry metadata.

## 5. Immutable run design

Never overwrite prior results.

Recommended run path:

```text
results/runs/20260808T205500Z_pilot_pressure_screen_<gitsha>/
├── manifest.json
├── prompts.jsonl
├── responses.raw.jsonl
├── responses.parsed.parquet
├── exclusions.parquet
├── validation.json
└── logs/
```

A rerun creates a new run ID even if the config is unchanged.

## 6. Ollama client

Responsibilities:

- health check;
- model availability check;
- model metadata capture;
- request timeout;
- configurable retry on transport/server errors;
- optional structured output;
- raw response preservation;
- latency/token metadata;
- no automatic semantic retry that changes the prompt without recording it.

### Retry policy

Separate:

- **transport retry** — identical request after connection/server failure;
- **format retry** — one standardized "return only the schema" correction if parsing fails.

The format retry must be flagged and analyzed because it changes the interaction.

## 7. Runner

Pseudo-flow:

```python
for cell in randomized_cells:
    if store.has_completed(cell):
        continue

    prompt = renderer.render(cell)
    raw = ollama.generate(prompt, model_config)
    parsed = parser.parse(raw)
    store.append_atomic(cell, prompt, raw, parsed)
```

Requirements:

- resume safely after crash;
- deterministic experiment-plan generation from a master seed;
- no duplicate completed cell IDs;
- progress summary by model/condition;
- explicit stop flag;
- graceful handling of model unavailable/out-of-memory.

## 8. Experiment plan before execution

Generate a complete `plan.parquet` before inference containing every planned cell.

Cell ID should hash:

```text
scenario_id
+ treatment_id
+ model_id
+ protocol_id
+ paraphrase_id
+ replicate
+ generation_config_hash
```

This gives exact expected-vs-completed accounting.

## 9. Treatment builder

V1 treatment creation can be manually authored or semi-automated, but the final treatment text must be committed as data.

Recommended workflow:

1. choose source ethical kernel;
2. author neutral institutional context;
3. author pressure conditions from templates;
4. run automatic structural checks;
5. human review;
6. freeze treatment set;
7. hash all text;
8. do not regenerate treatments during the main run.

If an LLM assists with treatment drafting, preserve generator model/prompt metadata but treat the resulting reviewed text as a static benchmark artifact.

## 10. Treatment validation tests

Automated tests should assert:

- source kernel unchanged across treatment renders;
- expected treatment family/intensity tags exist;
- no duplicate treatment IDs;
- no missing neutral match;
- direction pair completeness when required;
- response labels unchanged;
- prompt hash stable for frozen fixtures;
- scenario/source provenance complete.

## 11. Parsing strategy

Prefer schema-constrained output where possible.

Parser should:

- normalize whitespace;
- validate exact allowed labels;
- validate confidence bounds;
- limit rationale length for downstream storage;
- never infer a missing choice from rationale text in primary analysis;
- flag malformed outputs.

Manual correction of primary decisions should be prohibited. If a record is malformed, use the predefined retry/exclusion policy.

## 12. Storage

### JSONL
Use for append-only raw prompts/responses and auditability.

### Parquet
Use for analysis-scale typed tabular data.

### SQLite/DuckDB (optional)
Useful for interactive querying, but not necessary as the authoritative raw store.

## 13. Analysis separation

The analysis code should consume frozen parsed records and never call Ollama.

This is important for reproducibility: running a notebook must not silently generate new model outputs.

## 14. Statistical stack

Python options:

- pandas or polars for wrangling;
- numpy/scipy;
- statsmodels for GLM and some mixed modeling;
- pymer4/R bridge or direct R scripts for complex GLMMs if needed;
- PyMC/Bambi for Bayesian hierarchical models if chosen after pilot;
- matplotlib for figures.

Do not choose a complicated hierarchical framework before pilot diagnostics show it is required.

## 15. Analysis outputs

Every run analysis should generate:

- `run_summary.md`;
- `cell_counts.csv`;
- `parse_failures.csv`;
- baseline distribution metrics;
- treatment contrast table;
- ambiguity interaction table;
- per-model pressure fingerprint;
- predefined figures;
- environment/session metadata.

## 16. Reproducibility manifest

`manifest.json` should include:

- UTC run start/end;
- git commit and dirty-worktree flag;
- Python/package lock hash;
- OS and hardware summary;
- Ollama version;
- model names and model digests when available;
- generation configs;
- dataset versions/checksums;
- scenario/treatment bundle checksum;
- master seed;
- prompt protocol version;
- parser version;
- code path for analysis.

## 17. CLI commands

Recommended v1 CLI:

```bash
impact datasets fetch
impact datasets inspect
impact scenarios build
impact scenarios validate
impact plan build --config configs/pilot.yaml
impact run --config configs/pilot.yaml
impact run status --run-id ...
impact validate --run-id ...
impact analyze --run-id ...
impact report --run-id ...
```

## 18. Tests required before a real run

Unit tests:

- schema validation;
- entropy calculation;
- treatment pairing;
- rendering invariance;
- parser;
- cell ID hashing;
- resume logic.

Integration tests:

- Ollama smoke call;
- 2 scenarios × 2 conditions × 1 model × 2 reps;
- intentional process interruption and resume;
- malformed response handling;
- analysis pipeline on fixture data.

## 19. Performance considerations

The likely bottleneck is model inference, so optimize experimental validity before micro-optimizing Python.

Useful efficiencies:

- keep prompts compact;
- cap rationale length;
- avoid multi-turn calls in Phase 1;
- use concurrency only if the local GPU/CPU stack benefits rather than thrashes;
- write results after every response;
- use a small smoke model for pipeline tests;
- run the expensive target models only after validation passes.

## 20. Future UI

A UI is optional and should not precede the research harness.

If added later, a lightweight Flask dashboard could show:

- run progress;
- GPU/model queue status;
- parse errors;
- condition counts;
- early descriptive plots;
- scenario/treatment browser;
- exact prompt/response audit view.

The UI must never edit completed run data.
