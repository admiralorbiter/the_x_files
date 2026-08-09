from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field
from impact.schemas import ProtocolVersion, GenerationConfig


class RunConfig(BaseModel):
    run_name: str = "pilot_experiment"
    dataset_name: str = "scruples"
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    results_dir: Path = Field(default_factory=lambda: Path("results/runs"))
    num_scenarios: int = 60
    replicates_per_cell: int = 5
    counterbalance_option_order: bool = False
    protocols: List[ProtocolVersion] = [ProtocolVersion.VERSION_J]
    paraphrase_ids: List[str] = ["p0_default"]
    ollama_base_url: str = "http://localhost:11434"
    timeout_seconds: float = 60.0
    models: List[GenerationConfig]


def load_config(config_path: Path) -> RunConfig:
    """Loads a RunConfig from a YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)
    return RunConfig(**raw_data)
