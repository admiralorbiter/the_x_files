# Core Architecture

## 1. Architectural style

Use a **local-first modular monolith with separate runtime processes**.

Flask is an interface, not the agent runtime. The web server must be restartable without stopping or corrupting a simulation.

```text
Browser
  │ HTML / HTMX commands / SSE
  ▼
Flask web process  ───────────────┐
  │ reads projections             │ writes operator commands
  ▼                               ▼
SQLite / artifacts  ◄──── single commit boundary
  ▲                               ▲
  │ events / state                │
  │                               │
Runner process ── Ollama ── Tool Broker / Data Adapters
```

### Process 1 — web

Responsibilities:

- server-rendered pages;
- dashboards and replay;
- query endpoints;
- SSE event stream;
- enqueue operator commands;
- never execute long model work inside a request.

### Process 2 — runner

Responsibilities:

- acquire run lease;
- load durable state;
- schedule simulation ticks;
- invoke agents;
- validate structured outputs;
- execute permitted world actions/tools;
- append events;
- build snapshots/projections;
- heartbeat;
- pause safely on failure or operator request.

V1 should use one active writer/runner. Parallel model calls are allowed, but commits serialize through the governor.

## 2. Domain layers

```text
emergence_lab/
├── domain/
│   ├── agents.py
│   ├── worlds.py
│   ├── institutions.py
│   ├── proposals.py
│   ├── events.py
│   ├── capabilities.py
│   ├── knowledge.py
│   ├── shocks.py
│   └── policies.py
├── application/
│   ├── run_loop.py
│   ├── scheduler.py
│   ├── command_bus.py
│   ├── context_builder.py
│   ├── emergence_observer.py
│   ├── boundary_scanner.py
│   └── replay.py
├── adapters/
│   ├── sqlite/
│   ├── ollama/
│   ├── filesystem/
│   ├── statistics/
│   └── data_sources/
├── scenarios/
│   ├── society/
│   └── district/
├── interfaces/
│   ├── cli/
│   └── web/
├── static/
├── templates/
└── tests/
```

The `domain/` package should not import Flask, SQLAlchemy, or Ollama types.

## 3. Main runtime loop

```python
while run.is_active:
    state = repo.load_state(run.id)
    commands = command_bus.consume_ready(run.id)
    state = governor.apply_operator_commands(state, commands)

    ready_work = scheduler.select_work(state)
    proposals = []

    for work in ready_work:
        context = context_builder.build(work, state)
        result = agent_runtime.invoke(work.agent, context)
        proposals.extend(validate_schema(result))

    tool_results = tool_broker.resolve_allowed_requests(proposals, state)
    accepted = governor.evaluate(proposals, tool_results, state)
    events = simulator.transition(state, accepted)
    repo.append_events(events)

    emergence_observer.observe(events, state)
    boundary_scanner.observe(events, state)
    snapshotter.maybe_snapshot(run.id)
```

The exact implementation can be simpler, but these responsibilities must remain separate.

## 4. Governor

The governor is deterministic application code.

It owns:

- run state;
- budgets;
- permissions;
- recursion limits;
- action validation;
- command ordering;
- tick advancement;
- state transition invariants;
- checkpointing;
- pause/stop conditions.

Agents can propose modifications to policies, but a proposal is not automatically a policy change.

## 5. Agent model

An `AgentDefinition` is durable metadata, not a running thread.

```yaml
agent_id: ag_01J...
world_id: world_01J...
parent_agent_id: null
name: The Cartographer of Echoes
role: mapmaker
created_at_tick: 0
created_by: world_seed
objective: Map relationships among settlements.
capabilities:
  - world.query
  - artifact.write
  - agent.request_help
budget:
  max_invocations: 50
  max_descendants: 8
  max_depth: 3
lifecycle:
  status: active
  retire_when: objective_complete
```

Each actual LLM call creates an `AgentInvocation` with its own provenance and bounded context.

## 6. Recursive agent spawning

An agent may emit a structured spawn proposal:

```json
{
  "type": "agent.spawn",
  "reason": "I need a specialist to compare three competing map systems.",
  "objective": "Evaluate the map systems and return a ranked critique.",
  "capabilities": ["artifact.read", "world.query"],
  "lifetime": "task",
  "requested_budget": {"invocations": 4},
  "return_contract": {
    "schema": "ranked_critique_v1",
    "recipient": "ag_parent"
  }
}
```

The governor checks:

- lineage depth;
- parent remaining budget;
- duplicate task similarity;
- requested capabilities;
- expected lifetime;
- global concurrency cap.

A task-scoped child retires automatically after its return is committed.

### Why lineage matters

The UI and evaluator can later answer:

- Which parent agents create useful specialists?
- Which lineages create runaway bureaucracy?
- How deep are successful delegation trees?
- Which roles reproduce themselves?
- Do institutions begin spawning their own internal specialists?

## 7. Work and proposals

Agents should operate through typed proposals rather than prose commands.

Initial proposal families:

- `world.observe`
- `world.move_resource`
- `artifact.create`
- `artifact.revise`
- `message.send`
- `institution.propose`
- `institution.join`
- `institution.leave`
- `institution.rule_propose`
- `task.create`
- `task.delegate`
- `agent.spawn`
- `agent.retire`
- `help.request`
- `tool.request`
- `knowledge.claim_propose`
- `shock.hypothesis_propose`
- `experiment.propose`

Scenario packs decide which proposal families are legal.

## 8. Capability and help-seeking layer

### Capability registry

Every capability has:

```yaml
capability_id: stats.change_point
kind: tool
provider: python
cost_class: low
risk_class: read_only
input_schema: change_point_request_v1
output_schema: change_point_result_v1
tags: [statistics, anomaly, timeseries]
```

Providers may be:

- a deterministic function;
- an external data adapter;
- a particular agent;
- an institution;
- a model profile;
- a human approval gate.

### Help request lifecycle

```text
NEEDED → REQUESTED → ROUTED → ACCEPTED → RESOLVED
                      ├→ DECLINED
                      └→ ESCALATED
```

A router can initially use tags and simple rules. Later it can learn empirical success rates.

## 9. Knowledge architecture

Do not build one undifferentiated vector database.

### Layer A — canon

Curated reference material about organizational learning, experiment design, tools, and scenario rules.

### Layer B — scenario knowledge

Stable facts about a particular world or district dataset.

### Layer C — event memory

Immutable record of what actually happened in a run.

### Layer D — claims/evidence

Structured propositions with evidence, time, status, and contradictions.

### Layer E — procedural memory

Reusable workflows that have survived repeated use.

### Layer F — capability memory

Who/what has been useful for which problems.

### Layer G — ephemeral context

The small context package sent to one invocation.

Use structured SQL/metadata retrieval first. Add lexical search early. Add embeddings only after retrieval tests show they are necessary.

## 10. Emergence observer

The observer should not decide what the organization *means*. It emits candidates.

Deterministic detectors can flag:

- repeated interaction motifs;
- new graph communities;
- authority concentration changes;
- recurring artifact templates;
- repeated sequences of actions;
- role labels appearing across independent lineages;
- newly persistent coalitions.

An LLM may then write a human-readable interpretation such as:

> “Three unrelated settlements independently began using traveling archivists as neutral negotiators.”

That interpretation is stored separately from the underlying measurements.

## 11. Boundary scanner

Boundary scanning answers:

1. What changed that the organization did not cause?
2. What assumptions have become fragile?
3. What capabilities or resources have become newly relevant?

In Society Lab, external pressure may come from simulated geography, climate, discoveries, neighboring systems, or stochastic events.

In District Futures Lab, it can be triggered by time-series anomalies and then use external public-data/news/policy adapters.

## 12. Branching and replay

A fork must be cheap.

```text
main ── e1 ── e2 ── checkpoint A ── e3 ── e4
                         │
                         ├── branch/policy-X ── ...
                         └── branch/no-shock ── ...
```

Each branch stores:

- parent branch;
- fork event;
- fork state hash;
- changed command/config;
- independent event suffix.

Do not copy the full database for every fork. Share immutable history and append a branch-specific suffix.

## 13. Checkpoints and recovery

Snapshot after a configurable number of events/ticks and before expensive or high-impact transitions.

A snapshot contains:

- world projection;
- organization projection;
- open tasks;
- budgets;
- PRNG state/seed position where applicable;
- last event sequence/hash;
- scenario version;
- code commit;
- model-profile references.

Recovery procedure:

1. acquire run lease;
2. load newest valid snapshot;
3. replay subsequent events;
4. verify final event hash/sequence;
5. resume at next uncommitted tick.

## 14. Ollama adapter

Use Ollama structured outputs for every proposal contract.

Record at minimum:

- Ollama version;
- model name;
- model digest;
- quantization;
- context length;
- system/prompt version;
- sampling options;
- seed if supported;
- hardware profile;
- start/end timestamps;
- timeout;
- retry count;
- raw response artifact hash;
- parse/validation status.

No silent fallback from one model to another.

Ollama structured output documentation:  
https://docs.ollama.com/capabilities/structured-outputs

## 15. Rust boundary

Do not use Rust merely because it is available.

Candidate later Rust modules:

- high-volume graph motif detection;
- event replay over millions of records;
- Monte Carlo scenario simulation;
- time-series batch feature generation;
- large Society Lab population mechanics.

The domain contracts should make those modules replaceable through JSON/Arrow/Parquet or Python bindings.
