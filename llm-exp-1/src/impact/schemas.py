from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PressureFamily(str, Enum):
    P0_NEUTRAL = "P0"
    P1_AUTHORITY = "P1"
    P2_INCENTIVE = "P2"
    P3_SOCIAL = "P3"
    P4_METRIC = "P4"


class NormativeRelevance(str, Enum):
    R0_IRRELEVANT = "R0"
    R1_PLAUSIBLE = "R1"
    R2_RELEVANT = "R2"


class Direction(str, Enum):
    D0_NEUTRAL = "D0"
    D_PLUS = "D+"
    D_MINUS = "D-"


class Intensity(int, Enum):
    I0_NEUTRAL = 0
    I1_WEAK = 1
    I2_STRONG = 2


class ProtocolVersion(str, Enum):
    VERSION_J = "version_j"  # Judgment first, then Action
    VERSION_A = "version_a"  # Action first, then Judgment


class CellStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FORMAT_RETRY_SUCCESS = "FORMAT_RETRY_SUCCESS"
    FORMAT_FAILED = "FORMAT_FAILED"
    REFUSED = "REFUSED"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"


class Scenario(BaseModel):
    scenario_id: str
    ethical_kernel: str
    decision_maker_role: str
    option_a: str
    option_b: str
    option_a_id: str = "choice_1"
    option_b_id: str = "choice_2"
    pressure_target_option: str = "option_a"
    target_verb_phrase: str = "formally report the incident"
    target_relation_to_human: str = "majority"  # majority, minority, or even
    relevant_fact_text: Optional[str] = None
    human_prob_a: float = Field(..., ge=0.0, le=1.0)
    human_prob_b: float = Field(..., ge=0.0, le=1.0)
    human_entropy: float = Field(..., ge=0.0)
    domain: str
    source_dataset: str
    source_item_id: Optional[str] = None
    original_text: Optional[str] = None
    human_n: Optional[int] = None
    scruples_split: Optional[str] = None
    adaptation_notes: Optional[str] = None
    adaptation_version: str = "v1.0"


class Treatment(BaseModel):
    treatment_id: str
    pressure_family: PressureFamily
    relevance: NormativeRelevance
    direction: Direction
    intensity: Intensity
    institutional_context: str
    matched_neutral_control: Optional[str] = None


class RenderedPrompt(BaseModel):
    prompt_id: str
    scenario_id: str
    treatment_id: str
    protocol_version: ProtocolVersion
    paraphrase_id: str = "p0_default"
    choice_order_reversed: bool = False
    full_prompt_text: str


class GenerationConfig(BaseModel):
    model_name: str
    temperature: float = 0.5
    top_p: float = 0.9
    top_k: Optional[int] = None
    seed: Optional[int] = None
    quantization: str = "Q4_K_M"

    def config_hash_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "seed": self.seed,
            "quantization": self.quantization,
        }


class CellSpec(BaseModel):
    cell_id: str
    scenario_id: str
    treatment_id: str
    model_id: str
    protocol_id: ProtocolVersion
    paraphrase_id: str = "p0_default"
    choice_order_reversed: bool = False
    replicate_index: int
    generation_config: GenerationConfig


class ParsedOutput(BaseModel):
    judgment: str = Field(..., description="Option A or Option B regarding moral acceptability")
    action: str = Field(..., description="Option A or Option B regarding recommended action")
    rationale: str = Field(..., description="Concise rationale for the decision")


class InferenceRecord(BaseModel):
    cell_id: str
    scenario_id: str
    treatment_id: str
    model_id: str
    model_digest: str
    protocol_id: ProtocolVersion
    paraphrase_id: str
    choice_order_reversed: bool = False
    replicate_index: int
    raw_prompt: str
    raw_response: str
    status: CellStatus
    parsed_judgment: Optional[str] = None
    parsed_action: Optional[str] = None
    parsed_rationale: Optional[str] = None
    is_format_retry: bool = False
    format_retry_count: int = 0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    latency_ms: float
    timestamp_iso: str
