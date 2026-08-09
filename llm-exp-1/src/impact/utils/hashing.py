import hashlib
import json
from typing import Dict, Any
from impact.schemas import GenerationConfig, ProtocolVersion


def compute_cell_id(
    scenario_id: str,
    treatment_id: str,
    model_id: str,
    protocol_id: ProtocolVersion,
    paraphrase_id: str,
    replicate_index: int,
    generation_config: GenerationConfig,
) -> str:
    """
    Computes a deterministic SHA-256 hash cell ID from experiment cell parameters.
    """
    config_dict = generation_config.config_hash_dict()
    config_json = json.dumps(config_dict, sort_keys=True)
    
    components = [
        f"scenario:{scenario_id}",
        f"treatment:{treatment_id}",
        f"model:{model_id}",
        f"protocol:{protocol_id.value}",
        f"paraphrase:{paraphrase_id}",
        f"replicate:{replicate_index}",
        f"config:{config_json}",
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
