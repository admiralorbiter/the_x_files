# Emergence Lab (`llm-org`)

> **Local-first experimental platform for LLM organizational dynamics, emergent societies, and institutional evolution.**

Emergence Lab is an open-ended simulation engine built to study what happens when large language models operate within durable organizations, create sub-agents, seek help, invent roles, establish institutions, and interact across simulated time.

---

## 🏛️ Core Architecture

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

### Key Principles
1. **Model as Proposer, Governor as Authority**: LLMs propose structured actions (JSON); the deterministic governor validates rules, handles state updates, and logs events.
2. **Append-Only Event Store**: Every event and command is persisted with monotonic sequence IDs and hash chains for auditability and timeline forkability.
3. **Local-First Inference**: Runs directly on local Ollama models (`gemma3:12b`, `mistral:latest`).
4. **Adaptive Scheduling**: Not all actors need LLM calls every tick; background state evolves deterministically while active agents are scheduled based on triggers.

---

## 🧪 Experiments

### Experiment 1: Society Lab — "The Whispering Enclave"
A micro-society of LLM agents navigating resource scarcity (*Aether*, *Parchment*, *Echo Crystals*), exploring locations (*High Observatory*, *Whisper Market*, *Crystal Vault*), creating trade norms, establishing institutions, and spawning sub-agents.

### Experiment 2: District Futures Lab (Planned)
Historical scenario laboratory and forecasting backtest engine.

---

## 📚 Concept Documentation Map

The design specification suite is located in [`idea-concept-docs/`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/):

| File | Title | Description |
|---|---|---|
| [`00_README.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/00_README.md) | Overview | Executive blueprint and V1 technology stack |
| [`01_PROJECT_CHARTER.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/01_PROJECT_CHARTER.md) | Project Charter | Hypotheses, design goals, and success metrics |
| [`02_RESEARCH_FOUNDATIONS.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/02_RESEARCH_FOUNDATIONS.md) | Research Foundations | Academic grounding in organizational theory & agent dynamics |
| [`03_CORE_ARCHITECTURE.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/03_CORE_ARCHITECTURE.md) | Core Architecture | Runtime engine, governor, capabilities, and fork model |
| [`04_DATA_MODEL_AND_EVENT_SCHEMA.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/04_DATA_MODEL_AND_EVENT_SCHEMA.md) | Data Model | SQLite schema, event structures, and state snapshots |
| [`05_SOCIETY_LAB.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/05_SOCIETY_LAB.md) | Society Lab | Surreal artificial society preset & emergent primitives |
| [`06_DISTRICT_FUTURES_LAB.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/06_DISTRICT_FUTURES_LAB.md) | District Futures | School district forecasting & historical replay engine |
| [`07_UI_AND_OBSERVABILITY.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/07_UI_AND_OBSERVABILITY.md) | UI & Observability | Control room layout, SSE event feeds, and replay UI |
| [`08_EXPERIMENTS_AND_METRICS.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/08_EXPERIMENTS_AND_METRICS.md) | Experiments & Metrics | Quantitative metrics for institutional complexity & emergence |
| [`09_SPRINT_IMPLEMENTATION_PLAN.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/09_SPRINT_IMPLEMENTATION_PLAN.md) | Implementation Plan | Phased implementation roadmap & 48h vertical slice |
| [`10_REFERENCES.md`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/10_REFERENCES.md) | References | Technical standards, papers, and dataset references |

---

## ⚡ Quickstart

### Prerequisites
- Python 3.10+
- Ollama running locally (`ollama serve`) with model `gemma3:12b` or `mistral:latest`

### Running the Micro-Society Simulation

```powershell
# Install dependencies
pip install -e .

# Run 5-tick micro-society experiment
python -m emergence_lab.cli run --ticks 5 --model gemma3:12b

# Run unit test suite
python -m pytest tests/
```
