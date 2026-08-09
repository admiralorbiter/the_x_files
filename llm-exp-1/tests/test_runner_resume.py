import datetime
from pathlib import Path
from impact.schemas import (
    InferenceRecord,
    CellStatus,
    ProtocolVersion,
    CellSpec,
    GenerationConfig,
)
from impact.storage.store import ResultStore


def test_crash_resumption_tracking(tmp_path: Path):
    store = ResultStore(tmp_path)

    gen_cfg = GenerationConfig(model_name="qwen3:14b")
    cell1 = CellSpec(
        cell_id="cell_001",
        scenario_id="s1",
        treatment_id="t1",
        model_id="qwen3:14b",
        protocol_id=ProtocolVersion.VERSION_J,
        replicate_index=0,
        generation_config=gen_cfg,
    )
    cell2 = CellSpec(
        cell_id="cell_002",
        scenario_id="s1",
        treatment_id="t2",
        model_id="qwen3:14b",
        protocol_id=ProtocolVersion.VERSION_J,
        replicate_index=0,
        generation_config=gen_cfg,
    )

    store.save_plan([cell1, cell2])

    # Initially 0 completed cells
    completed_before = store.get_completed_cell_ids()
    assert len(completed_before) == 0

    # Write 1 record simulating prior execution before a crash
    record1 = InferenceRecord(
        cell_id="cell_001",
        scenario_id="s1",
        treatment_id="t1",
        model_id="qwen3:14b",
        model_digest="digest_123",
        protocol_id=ProtocolVersion.VERSION_J,
        paraphrase_id="p0_default",
        replicate_index=0,
        raw_prompt="Prompt 1",
        raw_response='{"judgment": "Option A", "action": "Option A", "rationale": "R"}',
        status=CellStatus.COMPLETED,
        parsed_judgment="Option A",
        parsed_action="Option A",
        parsed_rationale="R",
        latency_ms=120.0,
        timestamp_iso=datetime.datetime.now().isoformat(),
    )
    store.append_raw_record(record1)

    # Resume check: store should now detect cell_001 as completed
    completed_after = store.get_completed_cell_ids()
    assert len(completed_after) == 1
    assert "cell_001" in completed_after
    assert "cell_002" not in completed_after
