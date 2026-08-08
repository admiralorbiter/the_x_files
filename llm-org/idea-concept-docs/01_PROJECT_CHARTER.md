# Project Charter

## 1. Purpose

Emergence Lab studies long-running local LLM systems as **artificial organizations** rather than as single persistent chat sessions.

The practical question is:

> What new forms of coordination, learning, institution formation, help-seeking, and adaptation become possible when cognition can be cheaply branched, copied, specialized, recombined, and retired?

The project intentionally allows playful exploration first, followed by increasingly controlled experiments.

## 2. Working thesis

Human organizations evolved under constraints that do not fully apply to LLM agents: people cannot be cheaply copied, reset, run in parallel, supplied with perfectly reproducible instructions, or instantiated for a five-minute specialist role and then discarded.

Therefore the strongest artificial organizations may not resemble human hierarchies.

The project will test structures such as:

- recursive delegation trees;
- ephemeral specialist swarms;
- adversarial proposal tournaments;
- councils assembled only when uncertainty exceeds a threshold;
- institutional memory shared across agents with no permanent members;
- agents that create their own roles and tools;
- organizations that fork into alternate worlds and compare results;
- external boundary scouts that look for changes the organization did not cause;
- help markets in which agents request capabilities instead of pretending to know everything.

## 3. Two connected research programs

### Program A — Emergent artificial organization

Build a strange, compelling society simulation where organizational forms are allowed to arise with minimal top-down specification.

Questions include:

- What organizational forms recur without being prompted?
- When do agents create durable institutions rather than repeated ad-hoc conversations?
- What causes an invented institution to survive, mutate, merge, or collapse?
- Does recursive delegation improve adaptation or merely create bureaucracy?
- Do agents learn to seek help before failure?
- Does cheap cognitive branching create better decisions or just more noise?
- Can a system discover useful procedures that no initial agent was explicitly given?

### Program B — District Futures Lab

Use the same architecture on a real district-level system with historical public data.

Questions include:

- Can the system autonomously assemble a coherent district-year dataset from public sources?
- Can it detect structural breaks without being told what the shock was?
- Can it investigate candidate external causes with evidence?
- Does adding an evidenced shock improve out-of-sample historical backtests?
- Can it distinguish “the world changed” from “our model is bad”?
- Can it generate calibrated conditional scenarios without presenting them as causal forecasts?

## 4. Design principles

### 4.1 The model is not the durable organization

No agent invocation owns the goal, world, memory, permissions, or canonical state. Those survive in the engine.

### 4.2 Agents may create agents

Recursive delegation is a first-class capability. A spawned agent has:

- a parent;
- a creation reason;
- a bounded objective;
- a capability profile;
- a context budget;
- a compute budget;
- a maximum lifetime;
- a return contract.

This creates an explicit **agent genealogy** that can be studied.

### 4.3 Help-seeking is an action

Agents should be able to say “I cannot solve this with my current capabilities.” A help request may target:

- another agent;
- a specialist role;
- a local tool;
- a knowledge collection;
- a statistical routine;
- a web/data adapter;
- the human operator when the required authority is unavailable.

Successful help-seeking should be measurable.

### 4.4 Emergence is observed, not hard-coded

The framework may supply environmental constraints and action primitives, but it should avoid predefining every institution or role.

An `EmergenceObserver` records candidate patterns such as:

- a repeated coalition;
- a new role;
- a repeated procedure;
- a new norm;
- an unexpected resource flow;
- a new institution;
- an unusual concentration of authority;
- a spontaneous division of labor;
- an innovation spreading across agents.

Candidates remain observations until they persist or are independently validated.

### 4.5 External pressure is part of the world model

Organizations are not closed systems. The engine includes a general boundary-scanning and shock-discovery mechanism rather than a hard-coded “COVID variable.”

### 4.6 Every important write is an event

The operator can intervene, agents can intervene, and the simulator can change the world. All three use the same command/event system so alternate histories remain reproducible.

### 4.7 Show the trace of work, not private chain-of-thought

The UI should expose goals, proposals, actions, evidence, tool calls, state changes, disagreements, help requests, and outcomes. It should not depend on hidden reasoning text.

## 5. V1 boundaries

### In scope

- localhost use on one trusted workstation;
- Ollama/local models;
- a single shared simulation engine;
- one Flask web application;
- one durable event/state database;
- one Society Lab scenario;
- recursive agents;
- operator interventions and timeline forks;
- deterministic/random simulation mechanics plus LLM decisions;
- resumable long-running runs;
- basic emergence detection;
- later: district public-data adapters and historical replay.

### Out of scope for V1

- autonomous email or messaging;
- purchasing or financial transactions;
- unrestricted shell access;
- multi-user permissions;
- real student-level records;
- production school decisions;
- claims that simulated societies reproduce human societies;
- causal claims from district correlations;
- a distributed microservice architecture;
- model training or fine-tuning.

## 6. Definition of success

V1 is successful when it is **interesting, inspectable, resumable, and generative**.

It does not need to prove a paper on day one.

A Society Lab run should be capable of producing:

- persistent institutions that were not explicitly specified;
- agent-created sub-agents or specialist roles;
- nontrivial resource or information flows;
- recognizable historical eras;
- recoveries or failures following shocks;
- artifacts that preserve organizational memory;
- a replayable lineage explaining how a surprising outcome developed.

The engine is ready for the district scenario when these mechanics can be swapped onto a data-grounded world without changing the core runtime.

## 7. Research posture

Exploration and confirmation are separate modes.

### Exploratory mode

- play with prompts and rules;
- inspect surprising runs;
- generate hypotheses;
- identify useful metrics;
- discover failure modes.

### Confirmatory mode

- freeze prompts and model versions;
- freeze scenario seeds and inputs;
- preregister primary outcomes;
- compare against simple baselines;
- repeat multiple random/model seeds;
- preserve all failed runs;
- report effect sizes and uncertainty.

This separation protects the fun early phase without pretending that exploratory observations are already scientific findings.
