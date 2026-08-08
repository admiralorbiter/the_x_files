# Society Lab

## 1. Goal

Build an artificial society that is **fun to watch and capable of surprising its creator**.

This is not a model of normal human behavior. The world can contain strange species, impossible geography, living artifacts, unusual resources, or institutions that would make no sense in the real world.

The main research value is the organizational behavior that emerges when LLM agents are given durable state, recursive delegation, memory, help-seeking, limited resources, and the ability to invent institutions.

## 2. Default experiment: One Hundred Voices, One Century

A starting preset:

```yaml
scenario: society_lab
population: 100
simulated_years: 100
ticks_per_year: 4
initial_institutions: 0
initial_roles: minimal
world_seed: random
agent_activation:
  per_tick: adaptive_subset
recursive_spawning: true
operator_intervention: true
branching: true
external_shocks: procedural
```

The 100 actors do **not** all need an Ollama call every tick. Most world state can evolve deterministically. The scheduler activates agents when they have a reason to act.

That keeps a century computationally feasible and makes attention itself an organizational resource.

## 3. World ingredients

Start with enough structure to create pressure, but not enough to dictate institutions.

### Geography

Examples:

- floating islands that periodically change altitude;
- settlements connected by unreliable gates;
- a valley where written records slowly decay;
- migrating resource fields;
- regions with different physical rules.

### Resources

Use 4–8 resources with different properties:

- consumable;
- renewable;
- scarce;
- location-bound;
- knowledge-dependent;
- prestige-producing;
- dangerous when concentrated.

### Information

Information should be imperfectly distributed.

Some facts may be:

- locally observed;
- publicly recorded;
- disputed;
- forgotten;
- deliberately hidden by an institution;
- wrong because an earlier agent made an error.

### Initial actors

Give actors motives rather than occupations.

Examples:

- preserve fragile knowledge;
- accumulate beautiful objects;
- eliminate uncertainty;
- maximize autonomy;
- keep settlements connected;
- minimize conflict;
- explore unknown regions;
- protect a particular resource;
- create novelty;
- keep promises at all costs.

Let roles emerge from behavior.

## 4. Minimal action primitives

The simulator provides primitives; agents compose institutions from them.

- observe;
- move;
- gather/use/transfer resource;
- create/revise artifact;
- send message;
- make commitment;
- create task;
- delegate;
- spawn sub-agent;
- request help;
- form/join/leave/dissolve institution;
- propose institution rule;
- build tool;
- conduct experiment;
- negotiate exchange;
- challenge a claim;
- create archive.

Avoid hard-coding `create_government`, `create_bank`, `create_school`, or `create_religion`. If those appear, they should emerge from lower-level primitives and agent language.

## 5. LLM-native phenomena to encourage

### Ephemeral cognition

An institution can spawn a specialist for one problem and retire it immediately afterward.

Example:

> A council creates four temporary “future historians,” each simulates a different policy outcome, then the council synthesizes the branches and dissolves the historians.

### Cognitive branching

An agent may create competing sub-agents with mutually incompatible assumptions.

### Institutional reproduction

An institution may discover a successful internal process and create a new organization using the same charter template elsewhere.

### Role mutation

A role may fork into specialized descendants.

```text
Archivist
├── Conflict Archivist
├── Traveling Archivist
└── Memory Auditor
```

### Tool culture

An agent-created artifact can become a reusable organizational tool.

Examples:

- a treaty template;
- a risk ledger;
- a map convention;
- a voting ritual;
- a contradiction checklist;
- a resource-allocation algorithm.

The interesting outcome is not that the model wrote a document. It is that other agents adopt, modify, reject, or institutionalize it.

## 6. Shocks

Society Lab shocks should not all be pre-scripted narratives.

A procedural shock generator can alter parameters such as:

- resource regeneration;
- geography connectivity;
- communication reliability;
- artifact decay;
- migration;
- environmental risk;
- population needs;
- discovery of a new region or resource.

The system records the mechanical change but **agents do not have to receive its explanation**. They observe consequences and attempt to make sense of them.

This lets us study whether the organization detects that its environment changed.

## 7. Institutions as data

An institution has:

```yaml
institution_id: inst_...
name: The Quiet Cartographers
purpose: Resolve disagreements about maps.
founding_event: evt_...
charter_artifact: art_...
members: [...]
rules: [...]
resources: {...}
authority_scope: [...]
child_institutions: [...]
```

But its *type* should initially be free text plus learned classifications. A later observer can tag it as “guild-like,” “court-like,” “market-like,” etc. without forcing those categories at creation.

## 8. Activation scheduling

Calling 100 models four times per year for 100 years would be 40,000 actor turns before sub-agents. Instead use event-driven activation.

An agent enters the candidate pool when:

- a resource relevant to its motive changes;
- it receives a message;
- it owns an open commitment;
- an institution calls it;
- its plan reaches a scheduled time;
- it detects an anomaly;
- it is selected for periodic exploration;
- it is spawned for a task.

Then score candidates:

\[
Priority_i = w_1 Urgency_i + w_2 Relevance_i + w_3 Uncertainty_i + w_4 Novelty_i - w_5 RecentActivity_i.
\]

This is a scheduler heuristic, not a social-science claim.

## 9. Emergence observer outputs

Each simulated year should produce a compact “yearbook” containing:

- new institutions;
- dissolved institutions;
- new roles;
- repeated procedures;
- new tools/artifacts adopted by others;
- unexpected coalitions;
- largest authority shifts;
- biggest resource shifts;
- unresolved conflicts;
- interesting agent genealogies;
- observer hypotheses about what may be emerging.

Every narrative item links to the events behind it.

## 10. The Museum of Emergence

The end-of-run artifact should be fun enough to show people.

Possible sections:

- **Founding myths:** what the first decade invented;
- **Institution family tree:** who created whom;
- **The strangest durable rule:** a policy that survived 25+ years;
- **Lost technologies:** tools created then abandoned;
- **Great collapses:** institutions that failed rapidly;
- **Convergent inventions:** similar institutions invented independently;
- **Most consequential temporary agent:** a specialist that existed for one task but changed history;
- **The century in ten turning points:** generated from evidence-linked events;
- **Alternative histories:** branch comparisons from operator forks.

## 11. First presets

### Preset A — Blank civilization

Minimal knowledge, no institutions, moderate scarcity.

### Preset B — Perfect abundance, unreliable information

Resources are abundant but records contradict one another and decay.

### Preset C — Hard scarcity, perfect memory

Information is reliable; resource allocation is the main pressure.

### Preset D — The world changes its rules

Stable first 20 years, then several underlying environmental parameters shift without telling agents why.

### Preset E — Recursive cognition enabled/disabled

Same seed and world, but one branch permits recursive specialist spawning and one does not.

Preset E is already close to a publishable comparative experiment while remaining fun to watch.

## 12. Society Lab V1 acceptance test

A 20-year smoke run should:

- complete without manual repair;
- survive a runner restart;
- create at least one agent through delegation;
- create or reject at least one institution proposal;
- create at least one reusable artifact;
- generate help-request events;
- generate one procedural environmental shock;
- show state diffs in the UI;
- create a branch and replay it independently;
- produce an evidence-linked yearbook.

Do not require “good” emergence for the acceptance test. The system must work even when the society is boring or dysfunctional.
