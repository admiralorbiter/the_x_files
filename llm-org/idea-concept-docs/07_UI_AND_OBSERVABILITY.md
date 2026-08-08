# UI and Observability: The Emergence Control Room

## 1. Design goal

The interface should be something you **want to leave open while the system runs**.

It is not a chat window and not an admin CRUD dashboard. It is a mission-control interface for an artificial organization.

Use:

- Flask;
- Jinja templates;
- semantic HTML;
- custom CSS;
- HTMX for server-driven fragments and actions;
- Alpine.js for small local state and interactions;
- Server-Sent Events for live updates.

Avoid a SPA unless the interaction model eventually proves it necessary.

## 2. Do not display hidden chain-of-thought

Expose a **trace of work**:

- assigned objective;
- agent-visible context manifest;
- proposal summary;
- messages;
- tool/help requests;
- evidence used;
- decisions accepted/rejected by the governor;
- world-state changes;
- validation failures;
- generated artifacts;
- model/runtime metadata.

This is more trustworthy and more useful than a scrolling pseudo-mind-reading pane.

## 3. Main screen layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ EMERGENCE LAB  Run 27 | Year 38.2 | LIVE | Ollama ● | Pause | Fork │
├──────────────┬───────────────────────────────────┬──────────────────┤
│ WORLD PULSE  │           LIVING WORLD            │   AGENT GRAPH    │
│ metrics      │ map / institutions / resources    │ genealogy + org  │
│ warnings     │                                   │                  │
├──────────────┴───────────────────────────────────┴──────────────────┤
│                       EVENT RIVER                                  │
│ [agent] [proposal] [help] [institution] [shock] [operator] ...     │
├───────────────────────────────┬─────────────────────────────────────┤
│ BLACKBOARD / TASKS            │ EMERGENCE + BOUNDARY RADAR          │
│ active work + blockers        │ candidate patterns / anomalies      │
└───────────────────────────────┴─────────────────────────────────────┘
```

## 4. World Pulse

Large, glanceable values.

Society examples:

- simulated year;
- active population;
- active agents this tick;
- active institutions;
- new institutions this decade;
- role diversity;
- authority concentration;
- resource stress;
- open conflicts;
- open help requests;
- recursive agent depth;
- tokens/invocations this run.

District examples:

- replay year;
- data completeness;
- current forecast skill;
- interval coverage;
- unresolved structural breaks;
- evidence-backed shock candidates;
- fragile assumptions.

## 5. Event River

A live chronological feed, but with semantics.

Cards have distinct icons/types:

```text
12:14:03  AGENT SPAWN     Cartographer → Map Critic
12:14:08  HELP REQUEST    Needs conflict-resolution capability
12:14:12  INSTITUTION     Quiet Cartographers proposed
12:14:12  GOVERNOR        Proposal accepted
12:14:13  WORLD DIFF      +institution, +9 relationships
12:14:30  EMERGENCE       Independent mediator role seen in 3 regions
```

Clicking a card opens the causal trace.

## 6. Causal trace drawer

```text
Environmental event
   ↓
Agent activation
   ↓
Agent invocation
   ↓
Proposal
   ↓
Help/tool evidence
   ↓
Governor decision
   ↓
Committed world event
   ↓
Later dependent events
```

Include a “raw event JSON” disclosure for debugging.

## 7. Agent constellation and genealogy

Two graph modes:

### Organizational view

Nodes are current agents/institutions. Edges represent current relationships, messages, membership, dependency, or resource flow.

### Genealogy view

Shows recursive spawning:

```text
Founder
├─ Scout
│  ├─ Source Critic
│  └─ Weather Interpreter
└─ Archivist
   └─ Contradiction Auditor
```

Useful overlays:

- lifetime;
- compute cost;
- successful returned tasks;
- children count;
- help requests;
- institutional memberships.

V1 can use server-generated SVG with small vanilla/Alpine interactions. Do not add a heavy graph framework until necessary.

## 8. Blackboard

A structured work board:

- open questions;
- active tasks;
- blocked tasks;
- available proposals;
- unresolved contradictions;
- requested capabilities;
- candidate experiments.

It should look more like a research lab wall than Jira.

## 9. Emergence Radar

This panel contains machine-generated **candidates**, not declarations.

Examples:

```text
NEW PATTERN — 0.78
Traveling mediators appeared independently in 4 settlements.
Evidence: 17 events | first seen Year 12 | persistence 9 years
[Inspect] [Ask critic] [Track]
```

Categories:

- institution;
- role;
- procedure;
- coalition;
- tool;
- norm;
- authority shift;
- repeated failure;
- convergence;
- divergence.

## 10. Boundary / Shock Radar

```text
POSSIBLE EXTERNAL SHIFT
Metric cluster: attendance + enrollment + staffing
Window: 2019-20 → 2020-21
Detector score: 0.94
Status: investigating
Candidate external events: 3
[Open investigation]
```

For Society Lab, this shows environmental changes the agents are trying to explain.

## 11. Timeline scrubber

A major feature.

The user should be able to drag from Year 83 back to Year 17 and see:

- world snapshot;
- active institutions;
- agent population;
- metrics;
- event highlights;
- artifacts created up to that point.

Then choose **Fork from here**.

## 12. State diff viewer

Compare:

- tick to tick;
- year to year;
- before/after an intervention;
- main branch versus alternate branch.

Show structured changes before narrative explanation.

## 13. Artifact gallery

Agents may create:

- constitutions;
- maps;
- treaties;
- procedures;
- reports;
- theories;
- tools;
- datasets;
- district scenario reports.

The gallery shows version history, adopters, citations, and downstream events.

An artifact becomes fascinating when the UI can show that it was later reused by 14 other agents.

## 14. Operator write-backs

The UI should be able to write into the world through commands.

Initial controls:

- pause/resume run;
- change simulation speed;
- spawn a temporary observer/critic;
- ask for a counterargument;
- inject a scenario condition;
- add/remove a resource;
- create a new world fact;
- allocate extra budget to an agent/institution;
- request help on behalf of an agent;
- pin an artifact;
- fork timeline;
- terminate a runaway lineage;
- change an experiment flag.

Every button creates an `operator.*` command/event. There is no invisible puppeteering.

## 15. “Ask the world”

A small query box is useful if it is evidence-linked.

Examples:

- Why did the Archive Guild collapse?
- Which institutions benefited from the Year 31 resource shock?
- Who invented the mediator role first?
- Show three independent examples of the same procedure emerging.
- What changed after I forked the world at Year 20?

Answers should link to events/artifacts.

## 16. Next-morning view

When an overnight run completes, open to a curated summary:

### Overnight

- 43 simulated years advanced;
- 11 institutions formed;
- 4 dissolved;
- 37 temporary sub-agents spawned;
- 8 reusable tools created;
- 2 environmental shocks;
- 1 lineage stopped by budget guard;
- 5 candidate emergence patterns.

### Worth looking at

1. A temporary audit agent created in Year 22 produced a procedure still used in Year 61.
2. Two rival institutions independently invented nearly identical arbitration rules.
3. The population became more centralized after a communication shock and never fully decentralized.

This is the “wow” screen.

## 17. Live transport

Server-Sent Events are a good V1 choice because the dominant flow is server → browser.

Suggested endpoint:

```text
GET /runs/<run_id>/events/stream?after=<sequence>
Content-Type: text/event-stream
```

Use event sequence IDs for reconnect/resume.

HTMX SSE documentation:  
https://htmx.org/extensions/sse/

Flask streaming documentation:  
https://flask.palletsprojects.com/en/stable/patterns/streaming/

## 18. Page/blueprint structure

```text
web/
├── blueprints/
│   ├── home.py
│   ├── runs.py
│   ├── world.py
│   ├── agents.py
│   ├── institutions.py
│   ├── artifacts.py
│   ├── experiments.py
│   └── stream.py
├── templates/
│   ├── base.html
│   ├── control_room.html
│   ├── replay.html
│   └── partials/
└── static/
    ├── css/app.css
    └── js/app.js
```

Use Flask application factory and blueprints.

- https://flask.palletsprojects.com/en/stable/patterns/appfactories/
- https://flask.palletsprojects.com/en/stable/blueprints/

## 19. Visual style

Aim for “research observatory,” not enterprise SaaS.

- dark or neutral canvas;
- high-information but calm layout;
- strong typography;
- subtle motion only on newly arriving events;
- dense detail behind drawers;
- no fake typing animations;
- no chatbot bubbles as the primary interface;
- use color redundantly with icons/text so status remains accessible.

The interface should make the system feel alive because the **world is changing**, not because the UI is noisy.
