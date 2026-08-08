# Emergence Lab

**Status:** Working project blueprint  
**Date:** 2026-08-08  
**Working name:** Emergence Lab  

Emergence Lab is a local-first experimental platform for studying what happens when large language models are allowed to form temporary organizations, create sub-agents, seek help, invent procedures and institutions, react to changes in their environment, and continue working over long periods of simulated time.

The project deliberately starts on the **playful, generative side** rather than with a tightly benchmarked knowledge-base task. The first goal is to build something interesting enough to watch, perturb, fork, and learn from. Stronger research designs are layered on after the engine produces phenomena worth studying.

## Two scenario packs

### 1. Society Lab — build this first

A deliberately open, surreal artificial society. It does **not** need to model normal people faithfully. A default run may begin with roughly 100 actors and advance through decades or a century of simulated time. Actors can create organizations, norms, rituals, currencies, technologies, factions, archives, roles, councils, tools, and new agents.

The point is not to predict human society. The point is to create a rich environment in which **LLM-native forms of organization can emerge**.

### 2. District Futures Lab — build on the same engine later

A district-level education scenario laboratory grounded in public historical data. It begins with approximately ten years of historical district data, evaluates itself through rolling historical backtests, autonomously looks for external shocks and structural breaks, and then produces conditional ten-year future scenarios.

This is **scenario exploration, not deterministic prediction and not causal inference**.

## Core idea

The durable system is the organization. Individual LLM calls are temporary workers.

```text
charter + world state + event history + tools + budgets
                         │
                         ▼
                 deterministic governor
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       agents         tools/help     observers
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                 proposed state change
                         │
                         ▼
               validate → commit → log
                         │
                         ▼
                    next tick
```

Models can propose. The framework owns durable state, permissions, budgets, time, lineage, event history, and commits.

## What is intentionally LLM-native

Emergence Lab should not simply reproduce a human org chart. It should test affordances that are unusually cheap for language models:

- recursive sub-agent creation;
- rapid branching and parallel perspectives;
- temporary organizations that dissolve after one problem;
- agents that invent new roles instead of selecting from a fixed roster;
- explicit self-critique and adversarial review;
- automatic compression and synthesis of large organizational histories;
- help-seeking across a capability registry;
- tool creation and reuse;
- fast fork-and-replay of alternate histories;
- automatic boundary scanning for changes outside the organization;
- institutional memory that can outlive every individual agent.

## Architectural decisions carried forward from earlier project work

The existing project corpus already establishes useful design rules that should remain consistent here:

1. Prefer a **local-first modular monolith** over premature services.
2. Keep the domain/application layers independent of Flask, SQLAlchemy, or any model vendor.
3. Treat model output as a proposal rather than canonical truth or permission.
4. Preserve facts, claims, and events append-only; derived summaries and projections may be rebuilt.
5. Record causal event relationships, not only a chronological activity log.
6. Track valid time separately from recorded time when history matters.
7. Capture complete local-model provenance for reproducible Ollama runs.
8. Put consequential write operations through an explicit command/action boundary.

Relevant prior internal documents include `BIG_BRAIN_TIME_SYSTEM_BLUEPRINT.md`, `ARCHITECTURE_DECISION_RECORDS.md`, `BIG_BRAIN_TIME_DESIGN_STUDIO.md`, `handbook.md`, and `disagreement_aware_stem_feedback_master_plan.md`.

## Documentation map

| File | Purpose |
|---|---|
| `01_PROJECT_CHARTER.md` | vision, hypotheses, design principles, scope, success criteria |
| `02_RESEARCH_FOUNDATIONS.md` | organizational research, agent research, mathematical framing |
| `03_CORE_ARCHITECTURE.md` | runtime, governor, recursive agents, capabilities, knowledge, forks |
| `04_DATA_MODEL_AND_EVENT_SCHEMA.md` | SQLite model, events, world state, lineage, snapshots |
| `05_SOCIETY_LAB.md` | the first playable surreal society scenario |
| `06_DISTRICT_FUTURES_LAB.md` | district data, historical replay, forecasting, autonomous shock discovery |
| `07_UI_AND_OBSERVABILITY.md` | Flask/HTML/CSS/HTMX/Alpine control room and replay interface |
| `08_EXPERIMENTS_AND_METRICS.md` | exploratory and publishable experiments and measures |
| `09_SPRINT_IMPLEMENTATION_PLAN.md` | 48-hour vertical slice plus staged implementation roadmap |
| `10_REFERENCES.md` | research, official datasets, and technical references |

## Recommended V1 stack

- Python 3.12+
- Flask 3.x with application factory + blueprints
- Jinja templates
- HTMX for fragment updates and commands
- Alpine.js for small client-side state
- Server-Sent Events for live event streaming
- SQLAlchemy 2.x
- SQLite in WAL mode
- Pydantic 2.x for contracts and structured model output
- Ollama as the local inference service
- NumPy / pandas or Polars / statsmodels / scikit-learn for analysis
- Parquet for large analytical artifacts when the school scenario arrives
- Pytest
- Rust only after profiling shows a real bottleneck

Do **not** begin with React, Celery, Redis, Kafka, Kubernetes, a graph database, a vector database, or a custom Rust simulator. The first goal is a playable, inspectable system.

## First milestone

At the end of the first 48-hour build, a user should be able to:

1. create a Society Lab world from a seed;
2. run it for many ticks using local Ollama models;
3. see agents form, act, spawn sub-agents, request help, and create institutions;
4. watch a live event stream in Flask;
5. inspect an agent genealogy and world-state changes;
6. inject a condition or spawn a critic from the UI;
7. fork the timeline from any checkpoint;
8. stop the process and resume from durable state;
9. open a next-morning summary of what unexpectedly emerged.

That is enough to begin learning from the system before formalizing every research question.
