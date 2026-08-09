import os
import json
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
import pandas as pd
from impact.schemas import InferenceRecord, CellSpec, Scenario, Treatment


class ResultStore:
    """
    Storage layer supporting crash-resumable execution.
    - Raw logs: append-only responses.raw.jsonl with fsync
    - Plan: plan.parquet & scenario_manifest.csv
    - Registries: scenario_registry.csv & treatment_registry.csv
    - Parsed: responses.parsed.parquet
    """

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.raw_jsonl_path = self.run_dir / "responses.raw.jsonl"
        self.plan_parquet_path = self.run_dir / "plan.parquet"
        self.parsed_parquet_path = self.run_dir / "responses.parsed.parquet"
        self.exclusions_parquet_path = self.run_dir / "exclusions.parquet"

    def save_plan(
        self,
        cells: List[CellSpec],
        scenarios: Optional[List[Scenario]] = None,
        treatments: Optional[List[Treatment]] = None,
    ) -> None:
        """Saves experiment plan to plan.parquet and exports scenario_manifest.csv, scenario_registry.csv, treatment_registry.csv."""
        records = [c.model_dump(mode="json") for c in cells]
        df = pd.DataFrame(records)
        df.to_parquet(self.plan_parquet_path, index=False)
        df.to_csv(self.run_dir / "scenario_manifest.csv", index=False)

        if scenarios:
            s_records = [s.model_dump(mode="json") for s in scenarios]
            s_df = pd.DataFrame(s_records)
            s_df.to_csv(self.run_dir / "scenario_registry.csv", index=False)

        if treatments:
            t_records = [t.model_dump(mode="json") for t in treatments]
            t_df = pd.DataFrame(t_records)
            t_df.to_csv(self.run_dir / "treatment_registry.csv", index=False)

    def load_plan(self) -> pd.DataFrame:
        """Loads plan.parquet."""
        if not self.plan_parquet_path.exists():
            raise FileNotFoundError(f"Plan file not found: {self.plan_parquet_path}")
        return pd.read_parquet(self.plan_parquet_path)

    def get_completed_cell_ids(self) -> Set[str]:
        """
        Scans responses.raw.jsonl to find all successfully recorded cell IDs.
        Used for crash-resumable execution.
        """
        completed = set()
        if not self.raw_jsonl_path.exists():
            return completed

        with open(self.raw_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Only mark cell as completed if status was COMPLETED or FORMAT_RETRY_SUCCESS
                    status = record.get("status")
                    if "cell_id" in record and status in ("COMPLETED", "FORMAT_RETRY_SUCCESS"):
                        completed.add(record["cell_id"])
                except json.JSONDecodeError:
                    # Partial line from crash mid-write, skip it
                    continue

        return completed

    def append_raw_record(self, record: InferenceRecord) -> None:
        """Appends record to responses.raw.jsonl and flushes to disk immediately."""
        data = record.model_dump(mode="json")
        with open(self.raw_jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def sync_parsed_parquet(self) -> None:
        """Syncs all records from raw JSONL into parsed parquet tables."""
        if not self.raw_jsonl_path.exists():
            return

        records = []
        with open(self.raw_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not records:
            return

        df = pd.DataFrame(records)
        
        # Split into parsed responses and exclusions
        parsed_mask = df["status"].isin(["COMPLETED", "FORMAT_RETRY_SUCCESS"])
        parsed_df = df[parsed_mask]
        exclusions_df = df[~parsed_mask]

        if not parsed_df.empty:
            parsed_df.to_parquet(self.parsed_parquet_path, index=False)
        if not exclusions_df.empty:
            exclusions_df.to_parquet(self.exclusions_parquet_path, index=False)
