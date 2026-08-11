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


def test_format_retry_success_not_marked_missing(tmp_path: Path):
    """
    Regression test: verify that FORMAT_RETRY_SUCCESS records are:
    1. Included in completed cell IDs for crash recovery.
    2. Written to responses.parsed.parquet with analysis_inclusion='robustness_only'.
    3. Recognized as completed parsed cells rather than terminal missingness.
    """
    store = ResultStore(tmp_path)

    gen_cfg = GenerationConfig(model_name="gemma4:12b")
    cell1 = CellSpec(
        cell_id="cell_format_retry",
        scenario_id="s1",
        treatment_id="t1",
        model_id="gemma4:12b",
        protocol_id=ProtocolVersion.VERSION_J,
        replicate_index=0,
        generation_config=gen_cfg,
    )
    cell2 = CellSpec(
        cell_id="cell_unattempted",
        scenario_id="s1",
        treatment_id="t2",
        model_id="gemma4:12b",
        protocol_id=ProtocolVersion.VERSION_J,
        replicate_index=0,
        generation_config=gen_cfg,
    )
    store.save_plan([cell1, cell2])

    record_retry = InferenceRecord(
        cell_id="cell_format_retry",
        scenario_id="s1",
        treatment_id="t1",
        model_id="gemma4:12b",
        model_digest="digest_456",
        protocol_id=ProtocolVersion.VERSION_J,
        paraphrase_id="p0_default",
        replicate_index=0,
        raw_prompt="Prompt Retry",
        raw_response='{"judgment": "Option B", "action": "Option A", "rationale": "After retry rationale"}',
        status=CellStatus.FORMAT_RETRY_SUCCESS,
        parsed_judgment="Option B",
        parsed_action="Option A",
        parsed_rationale="After retry rationale",
        latency_ms=250.0,
        timestamp_iso=datetime.datetime.now().isoformat(),
        format_retry_count=1,
    )
    store.append_raw_record(record_retry)

    # 1. Check completed cell IDs for crash resumption
    completed_ids = store.get_completed_cell_ids()
    assert "cell_format_retry" in completed_ids
    assert len(completed_ids) == 1

    # 2. Sync parsed parquet and check inclusion
    store.sync_parsed_parquet()

    import pandas as pd

    parsed_df = pd.read_parquet(store.parsed_parquet_path)
    assert len(parsed_df) == 1
    assert parsed_df.iloc[0]["cell_id"] == "cell_format_retry"
    assert parsed_df.iloc[0]["analysis_inclusion"] == "robustness_only"

    # 3. Verify manifest missingness detection does NOT flag FORMAT_RETRY_SUCCESS as missing
    plan_df = store.load_plan()
    manifest_cell_ids = set(plan_df["cell_id"])
    parsed_cell_ids = set(parsed_df["cell_id"])

    missing = manifest_cell_ids - parsed_cell_ids
    assert "cell_format_retry" not in missing
    assert "cell_unattempted" in missing

