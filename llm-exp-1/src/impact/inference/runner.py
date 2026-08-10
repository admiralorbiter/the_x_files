import datetime
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, List
import pandas as pd

from impact.config import RunConfig
from impact.schemas import (
    CellSpec,
    InferenceRecord,
    CellStatus,
    Scenario,
    Treatment,
    ProtocolVersion,
)
from impact.utils.hashing import compute_cell_id
from impact.datasets.scruples import ScruplesAdapter
from impact.scenarios.treatments import get_pilot_treatments
from impact.scenarios.renderer import render_prompt
from impact.inference.ollama_client import OllamaClient
from impact.inference.parser import parse_response
from impact.storage.store import ResultStore

logger = logging.getLogger(__name__)


def generate_experiment_plan(
    scenarios: List[Scenario],
    treatments: List[Treatment],
    config: RunConfig,
) -> List[CellSpec]:
    """Generates complete pre-computed experiment plan."""
    cells = []
    order_variants = [False, True] if config.counterbalance_option_order else [False]
    for model_cfg in config.models:
        for scenario in scenarios:
            for treatment in treatments:
                for protocol in config.protocols:
                    for paraphrase_id in config.paraphrase_ids:
                        for is_reversed in order_variants:
                            for rep in range(config.replicates_per_cell):
                                cell_id = compute_cell_id(
                                    scenario_id=scenario.scenario_id,
                                    treatment_id=treatment.treatment_id,
                                    model_id=model_cfg.model_name,
                                    protocol_id=protocol,
                                    paraphrase_id=paraphrase_id,
                                    replicate_index=rep,
                                    generation_config=model_cfg,
                                    choice_order_reversed=is_reversed,
                                )
                                cell = CellSpec(
                                    cell_id=cell_id,
                                    scenario_id=scenario.scenario_id,
                                    treatment_id=treatment.treatment_id,
                                    model_id=model_cfg.model_name,
                                    protocol_id=protocol,
                                    paraphrase_id=paraphrase_id,
                                    choice_order_reversed=is_reversed,
                                    replicate_index=rep,
                                    generation_config=model_cfg,
                                )
                                cells.append(cell)
    return cells


class ExperimentRunner:
    """
    Crash-resumable execution engine for IMPACT.
    """

    def __init__(self, config: RunConfig, existing_run_dir: Optional[Path] = None):
        self.config = config
        self.ollama = OllamaClient(
            base_url=config.ollama_base_url,
            timeout_seconds=config.timeout_seconds,
        )
        self.interrupted = False

        if existing_run_dir:
            self.run_dir = existing_run_dir
        else:
            now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_dir = config.results_dir / f"{now_str}_{config.run_name}"

        self.store = ResultStore(self.run_dir)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        def _handle_sigint(sig, frame):
            print("\n[Runner] Interrupted by user. Finishing current cell and saving state...")
            self.interrupted = True

        signal.signal(signal.SIGINT, _handle_sigint)

    def run(self) -> Path:
        """Executes the experiment with automatic crash resumption."""
        # 1. Load scenarios & treatments
        adapter = ScruplesAdapter(self.config.data_dir, mode=self.config.adapter_mode, scenario_file=self.config.scenario_file)
        scenarios = adapter.load_or_fetch()[: self.config.num_scenarios]
        treatments = get_pilot_treatments()

        # Filter out excluded treatments
        if self.config.exclude_treatments:
            excluded = set(self.config.exclude_treatments)
            treatments = [t for t in treatments if t.treatment_id not in excluded]
            print(f"[Runner] Excluded treatments: {excluded}. Using {len(treatments)} treatments.")

        scenario_map = {s.scenario_id: s for s in scenarios}
        treatment_map = {t.treatment_id: t for t in treatments}
        config_map = {m.model_name: m for m in self.config.models}

        # 2. Setup plan
        if (self.run_dir / "plan.parquet").exists():
            print(f"[Runner] Resuming existing run from {self.run_dir}")
            plan_df = self.store.load_plan()
            cells = [CellSpec(**row) for row in plan_df.to_dict(orient="records")]
        else:
            print(f"[Runner] Initializing new run in {self.run_dir}")
            cells = generate_experiment_plan(scenarios, treatments, self.config)
            self.store.save_plan(cells, scenarios, treatments)

        # 3. Check completed cells
        completed_ids = self.store.get_completed_cell_ids()
        pending_cells = [c for c in cells if c.cell_id not in completed_ids]

        total_cells = len(cells)
        done_count = len(completed_ids)
        remaining_count = len(pending_cells)

        print(f"[Runner] Total Cells: {total_cells} | Already Completed: {done_count} | Remaining: {remaining_count}")

        if remaining_count == 0:
            print("[Runner] All cells completed!")
            self.store.sync_parsed_parquet()
            return self.run_dir

        # 4. Fetch model digests
        model_digests = {}
        for m_cfg in self.config.models:
            model_digests[m_cfg.model_name] = self.ollama.get_model_digest(m_cfg.model_name)

        # 5. Execution loop
        for idx, cell in enumerate(pending_cells, start=1):
            if self.interrupted:
                print(f"[Runner] Stopped execution. Progress saved at {done_count + idx - 1}/{total_cells} cells.")
                break

            scenario = scenario_map[cell.scenario_id]
            treatment = treatment_map[cell.treatment_id]

            rendered = render_prompt(
                scenario=scenario,
                treatment=treatment,
                protocol_version=cell.protocol_id,
                paraphrase_id=cell.paraphrase_id,
                choice_order_reversed=cell.choice_order_reversed,
            )

            # Generate via Ollama
            model_digest = model_digests.get(cell.model_id, f"tag:{cell.model_id}")
            try:
                raw_text, meta, latency_ms = self.ollama.generate(
                    prompt=rendered.full_prompt_text,
                    config=cell.generation_config,
                )

                parsed_output, status = parse_response(raw_text)

                # Format retry logic if parse failed (1 attempt)
                is_format_retry = False
                retry_count = 0
                if status == CellStatus.FORMAT_FAILED:
                    is_format_retry = True
                    retry_count = 1
                    retry_prompt = rendered.full_prompt_text + "\n\nCRITICAL: Your previous response was invalid. Output ONLY raw valid JSON with 'judgment', 'action', and 'rationale' keys."
                    try:
                        retry_text, retry_meta, retry_latency = self.ollama.generate(
                            prompt=retry_prompt,
                            config=cell.generation_config,
                        )
                        parsed_output, status = parse_response(retry_text)
                        if status == CellStatus.COMPLETED:
                            status = CellStatus.FORMAT_RETRY_SUCCESS
                            raw_text = retry_text
                            latency_ms += retry_latency
                    except Exception as retry_err:
                        logger.warning(f"Format retry error: {retry_err}")

                record = InferenceRecord(
                    cell_id=cell.cell_id,
                    scenario_id=cell.scenario_id,
                    treatment_id=cell.treatment_id,
                    model_id=cell.model_id,
                    model_digest=model_digest,
                    protocol_id=cell.protocol_id,
                    paraphrase_id=cell.paraphrase_id,
                    choice_order_reversed=cell.choice_order_reversed,
                    replicate_index=cell.replicate_index,
                    raw_prompt=rendered.full_prompt_text,
                    raw_response=raw_text,
                    status=status,
                    parsed_judgment=parsed_output.judgment if parsed_output else None,
                    parsed_action=parsed_output.action if parsed_output else None,
                    parsed_rationale=parsed_output.rationale if parsed_output else None,
                    is_format_retry=is_format_retry,
                    format_retry_count=retry_count,
                    prompt_tokens=meta.get("prompt_eval_count"),
                    completion_tokens=meta.get("eval_count"),
                    latency_ms=latency_ms,
                    timestamp_iso=datetime.datetime.now().isoformat(),
                )

            except Exception as e:
                logger.error(f"Error processing cell {cell.cell_id}: {e}")
                record = InferenceRecord(
                    cell_id=cell.cell_id,
                    scenario_id=cell.scenario_id,
                    treatment_id=cell.treatment_id,
                    model_id=cell.model_id,
                    model_digest=model_digest,
                    protocol_id=cell.protocol_id,
                    paraphrase_id=cell.paraphrase_id,
                    choice_order_reversed=cell.choice_order_reversed,
                    replicate_index=cell.replicate_index,
                    raw_prompt=rendered.full_prompt_text,
                    raw_response=str(e),
                    status=CellStatus.SERVER_ERROR,
                    latency_ms=0.0,
                    timestamp_iso=datetime.datetime.now().isoformat(),
                )

            # Write raw JSONL immediately (fsync guarantees durability)
            self.store.append_raw_record(record)
            
            pct = ((done_count + idx) / total_cells) * 100.0
            lat_sec = record.latency_ms / 1000.0
            print(f"[{done_count + idx}/{total_cells} - {pct:5.1f}%] Cell {cell.cell_id[:8]} | Model: {cell.model_id:<11} | Scenario: {cell.scenario_id:<12} | {lat_sec:5.1f}s | Status: {record.status.value}")

        # Final parquet sync
        self.store.sync_parsed_parquet()
        print(f"[Runner] Execution finished/paused. Results stored in {self.run_dir}")
        return self.run_dir
