# Sprint and Implementation Plan

## 1. Build strategy

Build the **smallest complete loop that is fun to watch**, then harden it.

Do not begin with the district data pipeline. Society Lab should prove the shared engine first.

The build sequence is:

```text
Durable event loop
    ↓
Ollama structured proposals
    ↓
Playable Society Lab
    ↓
Live control room
    ↓
Recursive agents + help seeking
    ↓
Emergence observation + forks
    ↓
District data adapters + replay
    ↓
Autonomous shock discovery
    ↓
Formal experiments
```

---

# Phase 0 — 48-Hour Playable Vertical Slice

This phase is intentionally concrete enough to start immediately.

## Day 1 — Make the world run

### Block 1 — repository skeleton

Create:

```text
emergence-lab/
├── pyproject.toml
├── README.md
├── instance/
├── data/
│   ├── artifacts/
│   └── runs/
├── emergence_lab/
│   ├── __init__.py
│   ├── config.py
│   ├── domain/
│   ├── application/
│   ├── adapters/
│   ├── scenarios/society/
│   └── interfaces/
└── tests/
```

Dependencies for the first commit:

- Flask
- SQLAlchemy
- Pydantic
- ollama Python client or direct HTTP client
- pytest
- python-dotenv only if needed for local configuration

**Acceptance:** `pytest` runs and `flask --app emergence_lab:create_app routes` works.

### Block 2 — durable event store

Implement:

- `runs`;
- `branches`;
- `events`;
- `commands`;
- `agents`;
- `agent_invocations`;
- `artifacts`;
- schema migration/version table.

Add:

- WAL mode;
- foreign keys;
- monotonic event sequence per branch;
- event hash chain;
- repository unit tests.

**Acceptance:** append 10,000 synthetic events, restart process, verify sequence/hash integrity.

### Block 3 — minimal world state

Implement a Society Lab state with:

- 3 locations;
- 4 resources;
- 10 smoke-test actors;
- relationships;
- simulated clock;
- simple deterministic resource regeneration/consumption.

Do not use Ollama yet.

**Acceptance:** 100 deterministic ticks replay to the same state from the same seed.

### Block 4 — Ollama structured proposal

Create one `SocietyActor` prompt and Pydantic output schema.

Initial legal proposals:

- observe;
- transfer resource;
- message;
- create artifact;
- create task;
- request help;
- spawn agent;
- propose institution.

Record full model provenance.

**Acceptance:** 20 model invocations produce valid typed outputs or bounded validation failures; no unhandled parse errors.

### Block 5 — governor + one tick

Flow:

```text
select active agents
→ build context
→ Ollama calls
→ proposals
→ validation
→ deterministic transition
→ append events
→ next tick
```

**Acceptance:** a ten-actor world runs 20 LLM-driven ticks entirely from CLI and can resume after process termination.

## Day 2 — Make it alive

### Block 6 — Flask control room

Implement pages:

- `/`
- `/runs`
- `/runs/<id>` control room
- `/runs/<id>/events`
- `/agents/<id>`
- `/artifacts/<id>`

Use Jinja, custom CSS, HTMX, Alpine.

**Acceptance:** the run can be inspected without opening SQLite manually.

### Block 7 — live SSE stream

Implement:

```text
GET /runs/<id>/events/stream?after=<sequence>
```

Client reconnects using sequence position.

**Acceptance:** new runner events appear in browser without page refresh; browser reconnect does not duplicate cards.

### Block 8 — recursive spawn

Implement bounded child creation:

- parent link;
- task objective;
- max depth = 2 initially;
- max 3 children per parent;
- tiny child budget;
- automatic retirement after return.

**Acceptance:** parent can create a child, child returns a structured artifact/result, lineage renders in UI.

### Block 9 — operator commands

Implement:

- pause/resume;
- spawn critic;
- inject resource change;
- fork current branch.

**Acceptance:** every UI action creates a command and later an `operator.*`/world event; direct hidden mutation is prohibited.

### Block 10 — overnight run

Scale to:

- 30–50 actors initially;
- event-driven activation;
- 50+ simulated years if compute permits;
- snapshots every N ticks;
- hard invocation budget.

Generate `overnight_report.md` from event data.

**48-hour Definition of Done:** a weird world evolves, the browser shows it live, recursive agents appear, the operator can intervene and fork, and the run survives restart.

---

# Sprint 1 — Engine Hardening

**Duration:** ~3–5 focused development days.

## Goals

Turn the vertical slice into a reliable experimental substrate.

## Work

### S1.1 Run leases and heartbeat

- one active runner per run;
- heartbeat timestamp;
- stale lease recovery;
- clean pause state.

### S1.2 Snapshot/replay

- snapshot state artifact;
- replay after snapshot;
- deterministic state hash;
- corrupted snapshot fallback.

### S1.3 Proposal contracts

- version every Pydantic schema;
- validation error events;
- retry policy by error class;
- no unlimited schema-repair loops.

### S1.4 Artifact store

- content-addressed paths;
- SHA-256 hash;
- metadata sidecar or DB row;
- Markdown/text/JSON support first.

### S1.5 Model profiles

- Ollama version and model digest capture;
- prompt bundles in versioned files;
- sampling config;
- request timeout;
- raw response retention.

### S1.6 Failure injection tests

Test:

- runner killed during model call;
- runner killed after proposal but before commit;
- malformed model output;
- Ollama unavailable;
- duplicate operator command;
- corrupted artifact reference.

## Definition of Done

A 100-tick test run can be deliberately killed several times and resume with no duplicate committed actions and no lost committed events.

---

# Sprint 2 — Society Emergence Mechanics

**Duration:** ~5 development days.

## Goals

Make the simulation richer without hard-coding a conventional society.

## Work

### S2.1 Institution primitive

- found;
- join/leave;
- charter artifact;
- resources;
- rules;
- dissolve;
- spawn tasks/agents.

### S2.2 Commitments and exchange

- promises/contracts;
- deadlines;
- resource exchange;
- broken commitment events.

### S2.3 Tool/procedure artifacts

Allow agents to publish reusable procedures and tools with adoption events.

### S2.4 Procedural shocks

Implement a generic environmental-parameter change generator.

Do not give agents the causal label.

### S2.5 Activation scheduler

Move from round-robin to relevance/event-driven activation.

### S2.6 World presets

Implement Blank Civilization, Fragile Memory, Scarcity, and Rule Change presets.

## Definition of Done

At least one 100-year run can complete within a configured compute budget and produce institution/tool/lineage histories with multiple distinct eras.

---

# Sprint 3 — Control Room, Replay, and Intervention

**Duration:** ~3–5 days.

## Goals

Make the project compelling to observe and manipulate.

## Work

### S3.1 Event River

- SSE;
- filters;
- expandable causal trace;
- raw event view.

### S3.2 Agent graph

- current organizational graph;
- genealogy mode;
- click-through detail.

### S3.3 Timeline scrubber

- yearly snapshots;
- historical world state;
- state diff.

### S3.4 Forks

- fork from checkpoint;
- branch comparison;
- operator label.

### S3.5 Artifact gallery

- artifact versions;
- adoption/citation history;
- creator/consumer graph.

### S3.6 Next-morning report

Evidence-linked summary and “worth looking at” cards.

## Definition of Done

A nontechnical viewer can watch a run, understand major events, inspect how one surprising institution formed, and compare two branches without reading logs.

---

# Sprint 4 — Recursive Organizations, Help, and Knowledge

**Duration:** ~5 days.

## Goals

Lean into LLM-specific leverage.

## Work

### S4.1 Capability registry

Providers, tags, risk, cost, schemas.

### S4.2 Help router

First version: deterministic matching by capability tags and availability.

### S4.3 Recursive delegation policies

- depth limits;
- subtree budgets;
- return contracts;
- duplicate-task detection;
- runaway-lineage termination.

### S4.4 Knowledge layers

- canon;
- scenario knowledge;
- event memory;
- claims/evidence;
- procedures;
- capability memory.

### S4.5 Emergence observer V1

Deterministic pattern candidates plus optional LLM narrative interpretation.

### S4.6 Procedure institutionalization

Track when artifacts/procedures are reused by unrelated agents or institutions.

## Definition of Done

The UI can show a complete story such as:

> An agent hit a blocker, requested expertise, spawned a specialist, received a procedure, and that procedure later spread to unrelated institutions.

---

# Sprint 5 — District Public-Data Foundation

**Duration:** ~1–2 weeks depending on source friction.

## Goals

Build the district scenario without compromising the general engine.

## Work

### S5.1 District identity spine

Use NCES LEA IDs as the primary cross-source district identifier where applicable.

Create crosswalk tables for state IDs and district names.

### S5.2 Initial adapters

Prioritize:

1. NCES CCD LEA universe;
2. NCES F-33 finance;
3. Census SAIPE API;
4. Missouri DESE or Kansas KSDE for the first local pilot;
5. EDFacts chronic absenteeism/selected outcomes.

Do not integrate every possible source at once.

### S5.3 Raw artifact freezer

- content hashes;
- release dates;
- retrieval date;
- parser version;
- source metadata.

### S5.4 Metric Passports

Create a registry and validation rules.

### S5.5 District-year analytical table

Export canonical analytical snapshots to Parquet.

### S5.6 Baselines

Implement last-value, trend, and ridge baselines.

### S5.7 Rolling replay engine

Simulated as-of dates and data-release filtering.

## Definition of Done

For one district and at least 8 historical years, the system can recreate a dataset as of each replay origin and produce leakage-free baseline forecasts with provenance.

---

# Sprint 6 — Autonomous Boundary and Shock Discovery

**Duration:** ~1 week.

## Goals

Make the system discover external pressure instead of receiving manual shock labels.

## Work

### S6.1 Detector ensemble

- standardized residual threshold;
- CUSUM;
- offline change-point analysis;
- Bayesian online detector prototype.

### S6.2 Shock footprint object

- metrics;
- geography;
- time window;
- direction;
- synchrony;
- missingness pattern.

### S6.3 Research query generator

LLM converts footprint to multiple neutral search hypotheses.

### S6.4 External adapters

Start with:

- upstream GDELT discovery;
- OpenFEMA;
- BLS/Census context;
- official state/federal policy pages.

### S6.5 Evidence ledger

Each event candidate carries publication time and geography.

### S6.6 Shock feature tests

Predefined pulse/step/ramp encodings; nested rolling backtests.

### S6.7 COVID diagnostic replay

Run historical replay through 2019–2022 **without a manual COVID feature**.

## Definition of Done

The system detects a material break, autonomously researches plausible external events using only as-of evidence, and records whether those events improve post-break model performance.

---

# Sprint 7 — Research Hardening

**Duration:** ~1 week for the first study package.

## Goals

Turn interesting observations into reproducible experiments.

## Work

- experiment manifests;
- frozen scenario/config files;
- seed sweeps;
- model-profile comparison;
- compute accounting;
- metric definitions and versions;
- automatic result tables;
- failure taxonomy;
- preregistration template;
- exportable run bundle;
- paper figure scripts.

## First candidate study

**Recursive organization under environmental change**

Conditions:

1. flat/no sub-agents;
2. bounded one-level delegation;
3. bounded recursive delegation.

Run across multiple world seeds and at least two local Ollama models.

Measure:

- shock recovery;
- compute;
- institution survival;
- help use;
- delegation overhead;
- structural diversity.

---

# Implementation details

## Flask application

Use an application factory:

```python
def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    # load config
    # init db/read services
    # register blueprints
    return app
```

Keep routes thin.

## Runner entrypoint

```bash
python -m emergence_lab.runner --run RUN_ID
```

The runner can be launched manually during development. Do not add a distributed task queue in V1.

## Useful CLI commands

```bash
flask --app emergence_lab:create_app run
python -m emergence_lab.runner create --scenario society
python -m emergence_lab.runner start RUN_ID
python -m emergence_lab.runner replay RUN_ID
python -m emergence_lab.runner verify RUN_ID
python -m emergence_lab.runner report RUN_ID
```

## Configuration hierarchy

```text
base config
→ model profile
→ scenario config
→ experiment manifest
→ branch/operator overrides
```

All overrides are recorded.

---

# Testing strategy

## Unit tests

- proposal validators;
- state transitions;
- budget rules;
- lineage limits;
- capability routing;
- event hashing;
- as-of filters;
- metric calculations.

## Property tests

Useful invariants:

- resources cannot become negative unless scenario permits debt;
- one event sequence cannot appear twice in a branch;
- committed event hash chain must verify;
- child lineage depth = parent depth + 1;
- retired agents cannot initiate new actions;
- replay(state_0, events) = current_state;
- district replay never sees a future release.

## Integration tests

- Ollama schema output;
- runner restart;
- SSE reconnect;
- branch fork;
- artifact read/write;
- public data adapter fixture replay.

## Golden runs

Keep tiny fixed worlds with captured proposals/events so UI and replay can be regression-tested without invoking Ollama.

---

# What not to build yet

Explicitly defer:

- React/Vue/Svelte SPA;
- Redis;
- Celery;
- Kafka;
- Kubernetes;
- multiple database servers;
- graph database;
- default vector database;
- unrestricted browser automation;
- unrestricted shell tool;
- custom Rust runtime;
- student-level educational data;
- automatic causal inference;
- fine-tuning.

Every deferred component can be added later behind an existing port if measurements justify it.

---

# Immediate implementation checklist

If starting now, do these in order:

- [ ] Initialize Python package and Flask app factory.
- [ ] Create SQLite schema + migrations/versioning.
- [ ] Implement append-event + event hash chain.
- [ ] Implement deterministic SocietyWorld and replay test.
- [ ] Build Ollama `ProposalEnvelope` schema.
- [ ] Add one agent invocation and raw-response artifact capture.
- [ ] Implement governor accepting/rejecting proposal types.
- [ ] Run ten LLM-driven ticks from CLI.
- [ ] Add `run`, `agent`, and `event` Flask views.
- [ ] Stream new events via SSE.
- [ ] Add recursive `agent.spawn` with depth/budget limits.
- [ ] Add pause/resume/operator command.
- [ ] Add fork command.
- [ ] Run the first overnight experiment.
- [ ] Read the next-morning report before adding more architecture.

The last item is important: **let the first real run teach you what to build next.**
