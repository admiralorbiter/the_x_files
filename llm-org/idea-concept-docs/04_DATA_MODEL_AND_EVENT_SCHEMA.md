# Data Model and Event Schema

## 1. Storage strategy

Use SQLite as the operational store for V1 with WAL enabled.

The system is event-centered but pragmatic:

- immutable events provide history and causality;
- normalized operational tables provide efficient current-state queries;
- snapshots speed recovery;
- large numerical outputs can live in Parquet/files referenced by hash;
- raw model outputs are artifacts, not giant SQLite text blobs when they become large.

V1 uses a single writer through the runner/governor.

## 2. Time model

Several times must remain distinct.

| Field | Meaning |
|---|---|
| `sim_time` | time inside the simulated world |
| `valid_from` / `valid_to` | when a claim/state is true in the represented world |
| `observed_at` | when an observation was made |
| `occurred_at` | wall-clock time an engine event occurred |
| `recorded_at` | wall-clock time it entered the ledger |
| `published_at` | source publication time; essential for historical replay |

District backtests must filter external evidence on `published_at <= replay_as_of`.

## 3. Core tables

### `runs`

- `run_id`
- `scenario_id`
- `scenario_version`
- `status`
- `created_at`
- `started_at`
- `stopped_at`
- `current_branch_id`
- `current_tick`
- `seed`
- `config_json`
- `code_commit`

### `branches`

- `branch_id`
- `run_id`
- `parent_branch_id`
- `fork_event_id`
- `fork_reason`
- `created_at`
- `operator_label`

### `events`

- `event_id`
- `run_id`
- `branch_id`
- `sequence`
- `sim_time`
- `event_type`
- `actor_type`
- `actor_id`
- `subject_type`
- `subject_id`
- `parent_event_id`
- `trace_id`
- `payload_json`
- `occurred_at`
- `recorded_at`
- `previous_event_hash`
- `event_hash`

### `agents`

- `agent_id`
- `run_id`
- `branch_id`
- `parent_agent_id`
- `spawn_event_id`
- `name`
- `role`
- `objective`
- `status`
- `created_tick`
- `retired_tick`
- `lineage_depth`
- `capability_profile_json`
- `budget_json`

### `agent_invocations`

- `invocation_id`
- `agent_id`
- `task_id`
- `model_profile_id`
- `prompt_version`
- `context_manifest_hash`
- `raw_response_artifact_id`
- `started_at`
- `finished_at`
- `status`
- `retry_of_invocation_id`

### `tasks`

- `task_id`
- `parent_task_id`
- `created_by_agent_id`
- `assigned_agent_id`
- `objective`
- `status`
- `priority`
- `deadline_sim_time`
- `return_contract_json`
- `budget_json`

### `proposals`

- `proposal_id`
- `invocation_id`
- `proposal_type`
- `payload_json`
- `status`
- `validation_errors_json`
- `accepted_event_id`

### `institutions`

- `institution_id`
- `institution_type`
- `name`
- `founded_event_id`
- `dissolved_event_id`
- `charter_artifact_id`
- `status`

### `institution_memberships`

- `institution_id`
- `agent_id`
- `role`
- `valid_from_tick`
- `valid_to_tick`

### `world_entities`

Generic scenario-defined entities such as settlements, districts, resources, species, programs, facilities, or policies.

- `entity_id`
- `entity_type`
- `name`
- `state_json`
- `created_event_id`
- `retired_event_id`

### `relationships`

- `relationship_id`
- `subject_id`
- `predicate`
- `object_id`
- `weight`
- `valid_from_tick`
- `valid_to_tick`
- `source_event_id`

### `capabilities`

- `capability_id`
- `kind`
- `provider_ref`
- `risk_class`
- `cost_class`
- `input_schema_version`
- `output_schema_version`
- `tags_json`

### `help_requests`

- `help_request_id`
- `requester_agent_id`
- `task_id`
- `need`
- `requested_capability_tags_json`
- `status`
- `routed_to`
- `created_tick`
- `resolved_tick`
- `result_artifact_id`

### `claims`

Claims are append-only.

- `claim_id`
- `subject`
- `predicate`
- `object_json`
- `polarity`
- `epistemic_class`
- `confidence`
- `valid_from`
- `valid_to`
- `recorded_at`
- `status`
- `created_by`

### `evidence_links`

- `claim_id`
- `artifact_id`
- `locator`
- `support_type`
- `source_authority`

### `shock_candidates`

- `shock_id`
- `run_id`
- `detected_from_metric`
- `change_window_start`
- `change_window_end`
- `detector`
- `detector_score`
- `status`
- `hypothesis_summary`
- `mechanism_json`
- `evidence_count`
- `backtest_uplift`

### `artifacts`

- `artifact_id`
- `content_hash`
- `media_type`
- `path`
- `created_by`
- `created_at`
- `metadata_json`

### `commands`

Operator/UI write-backs.

- `command_id`
- `run_id`
- `branch_id`
- `command_type`
- `payload_json`
- `issued_by`
- `issued_at`
- `status`
- `processed_event_id`

### `snapshots`

- `snapshot_id`
- `run_id`
- `branch_id`
- `through_sequence`
- `through_tick`
- `state_artifact_id`
- `state_hash`
- `created_at`

### `metrics`

- `metric_id`
- `run_id`
- `branch_id`
- `sim_time`
- `metric_name`
- `value`
- `dimensions_json`
- `definition_version`

## 4. Canonical event envelope

```json
{
  "schema_version": "1.0",
  "event_id": "evt_01J...",
  "run_id": "run_01J...",
  "branch_id": "br_main",
  "sequence": 1842,
  "sim_time": "YEAR:37/SEASON:2",
  "event_type": "institution.founded",
  "trace_id": "tr_01J...",
  "parent_event_id": "evt_01J...",
  "actor": {
    "type": "agent",
    "id": "ag_01J..."
  },
  "subject": {
    "type": "institution",
    "id": "inst_01J..."
  },
  "payload": {
    "name": "The Quiet Cartographers",
    "purpose": "Resolve conflicting maps without coercion",
    "member_ids": ["ag_a", "ag_b", "ag_c"]
  },
  "occurred_at": "2026-08-08T18:20:01Z",
  "recorded_at": "2026-08-08T18:20:01Z",
  "integrity": {
    "previous_event_hash": "sha256:...",
    "event_hash": "sha256:..."
  }
}
```

## 5. Event families

Do not collapse everything into `agent_action`.

```text
run.*
branch.*
tick.*
agent.spawned
agent.retired
agent.invocation.*
task.*
proposal.*
help.*
tool.*
message.*
resource.*
institution.*
relationship.*
artifact.*
claim.*
evidence.*
shock.*
emergence.*
operator.*
verification.*
snapshot.*
error.*
```

## 6. Causal trace

Every consequential event should answer:

- What caused this?
- Which proposal or command led to it?
- Which invocation created the proposal?
- Which evidence or tool result influenced it?
- Which state changed?
- What later events depend on it?

This enables the UI to display a meaningful trace without exposing hidden model reasoning.

## 7. Projections

Useful current-state projections include:

- active agents;
- active institutions;
- current world resources;
- task board;
- agent genealogy;
- institution membership graph;
- latest metric values;
- open help requests;
- unresolved shock candidates;
- emergence candidates;
- run health.

Projection tables may be rebuilt from the event log and snapshots.

## 8. State diffs

Every tick should be able to render a compact diff:

```yaml
resources:
  moon_salt: +14
institutions:
  created: [inst_quiet_cartographers]
  dissolved: []
agents:
  spawned: [ag_map_critic]
  retired: [ag_temp_mediator]
relationships:
  added: 9
  removed: 2
metrics:
  authority_hhi: 0.18 -> 0.24
  role_entropy: 1.72 -> 1.89
```

That diff is a first-class UI artifact and a useful context input for observer agents.

## 9. Model provenance profile

A `model_profiles` record should include:

```yaml
provider: ollama
ollama_version: 0.x.x
model: qwen3:14b
model_digest: sha256:...
quantization: Q4_K_M
context_length: 32768
sampling:
  temperature: 0.6
  top_p: 0.9
prompt_bundle_version: society-v003
hardware:
  gpu: local
  vram_gb: 16
```

Every invocation references the profile rather than duplicating it.

## 10. Retention

Keep indefinitely for research runs:

- scenario configuration;
- accepted events;
- model provenance;
- prompts by version;
- raw responses or hashes plus retained raw files;
- metrics;
- errors;
- operator commands;
- branch ancestry.

Allow compacting/rebuilding:

- dashboards;
- summaries;
- embeddings;
- graph projections;
- context packs.
