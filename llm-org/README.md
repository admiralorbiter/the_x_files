# Emergence Lab (`llm-org`)

> **Local-first experimental platform for LLM organizational dynamics, emergent societies, and institutional evolution.**

Emergence Lab is an open-ended simulation engine built to study what happens when large language models operate within durable organizations, create sub-agents, seek help, invent roles, establish institutions, and interact across simulated time.

---

## 🗺️ Roadmap & Features Developed So Far

- [x] **Core Architecture & Governor Engine** ([`emergence_lab/engine/governor.py`](file:///c:/Users/admir/Github/the_x_files/llm-org/emergence_lab/engine/governor.py)): Model-as-proposer, governor-as-authority deterministic execution engine.
- [x] **Append-Only SQLite Event Store with SHA-256 Hashing** ([`emergence_lab/adapters/db.py`](file:///c:/Users/admir/Github/the_x_files/llm-org/emergence_lab/adapters/db.py)): WAL mode SQLite database tracking runs, events, and state snapshots with cryptographic sequence hash integrity.
- [x] **4-Stage Resilient Ollama Client** ([`emergence_lab/adapters/ollama_client.py`](file:///c:/Users/admir/Github/the_x_files/llm-org/emergence_lab/adapters/ollama_client.py)): Fault-tolerant client that handles Ollama CUDA/grammar bugs using unconstrained mode fallbacks and regex JSON extraction.
- [x] **Pydantic v2 Schema Coercion** ([`emergence_lab/domain/events.py`](file:///c:/Users/admir/Github/the_x_files/llm-org/emergence_lab/domain/events.py)): Automatic coercion for single and group targets (e.g. `['Plato', 'Heraclitus']` -> `"Plato, Heraclitus"`).
- [x] **Procedural Shock & Topic Engine** ([`emergence_lab/engine/topics.py`](file:///c:/Users/admir/Github/the_x_files/llm-org/emergence_lab/engine/topics.py)): Injects random world events every 3 ticks and rotates through dynamic philosophical topic domains (Epistemology, Ethics, AI Consciousness, Metaphysics, Free Will).
- [x] **"Synthesize or Fork" Impasse Mandate**: Prevents LLMs from getting trapped in infinite dialogue loops by forcing written `Artifact` creation, sub-agent `Disciple` spawning, or `Institution` founding when speech stalls.
- [x] **Multi-Scenario Support**:
  - **`socratic` (Socratic Academy: The Dialectic Grove)**: Philosophical inquiry with *Socrates*, *Plato*, and *Heraclitus*.
  - **`micro` (Society Lab: The Whispering Enclave)**: Resource trade, scarcity, and micro-society governance.
- [x] **Automated Test Suite** ([`tests/`](file:///c:/Users/admir/Github/the_x_files/llm-org/tests/)): 6/6 passing unit tests covering event hashing, action application, list coercion, and prompt assembly.
- [ ] **Web Control Room UI** *(Upcoming)*: Flask + SSE + HTMX live event stream and replay control room.
- [ ] **Timeline Forking & Branch Replay** *(Upcoming)*: Branching alternate world histories from past SQLite checkpoints.
- [ ] **District Futures Lab Scenario** *(Upcoming)*: School district scenario & historical replay engine.

---

## 🏛️ Core System Architecture

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

---

## 🖥️ Setup Guide for Other Computers & Different Ollama Models

### 1. Prerequisites
- Python **3.10+**
- [Ollama](https://ollama.com/) installed and running locally (`ollama serve`) or accessible on your local network.

### 2. Installation
Clone the repository and install the dependencies:

```powershell
# Navigate to the project directory
cd llm-org

# Install package in editable mode
pip install -e .
```

### 3. Ollama Model Setup
Emergence Lab works with **any model in Ollama**! You can pull your preferred models:

```powershell
# Recommended Fast 7B Model
ollama pull mistral:latest

# Recommended Reasoning / Roleplay 12B Model
ollama pull gemma3:12b

# Alternative Models
ollama pull llama3:8b
ollama pull qwen2.5:7b
```

### 4. Configuration (Environment Variables)
You can configure custom Ollama hosts or default models using environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL of local or remote Ollama server |
| `OLLAMA_MODEL` | `gemma3:12b` | Default primary model |
| `OLLAMA_FALLBACK_MODEL` | `mistral:latest` | Default fallback model if primary fails |
| `EMERGENCE_DB_PATH` | `emergence_lab.db` | Path to SQLite database file |

---

## ⚡ Execution & Command Reference

### Running Simulations via CLI

#### Run the Socratic Academy (Default Scenario):
```powershell
python -u -m emergence_lab.cli run --ticks 10 --scenario socratic --model mistral:latest
```

#### Run with Gemma 3 12B:
```powershell
python -u -m emergence_lab.cli run --ticks 10 --scenario socratic --model gemma3:12b
```

#### Run the Whispering Enclave Micro-Society Scenario:
```powershell
python -u -m emergence_lab.cli run --ticks 10 --scenario micro --model mistral:latest
```

### Running the Test Suite
```powershell
python -m pytest tests/
```

### Querying the Event Database
All events and state snapshots are saved in `emergence_lab.db` (in SQLite WAL mode):

```python
import sqlite3, json

conn = sqlite3.connect("emergence_lab.db")
events = conn.execute("SELECT tick, actor_id, event_type, payload FROM events ORDER BY id DESC LIMIT 10").fetchall()
for e in events:
    print(f"Tick {e[0]} | {e[1]} -> {e[2]}: {e[3]}")
```

---

## 📚 Concept Documentation Index

The full specification suite is located in [`idea-concept-docs/`](file:///c:/Users/admir/Github/the_x_files/llm-org/idea-concept-docs/):

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
