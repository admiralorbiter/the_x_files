"""Telemetry and Provenance tracking for Emergence Lab inference engine."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class InferenceResult(BaseModel):
    requested_model: str
    actual_model: str
    attempts: int = 1
    prompt_tokens: Optional[int] = None
    eval_tokens: Optional[int] = None
    duration_ms: float = 0.0
    validation_status: Literal["valid", "repaired", "failed"] = "valid"
    repairs_applied: List[str] = Field(default_factory=list)
    fallback_used: bool = False
    error_message: Optional[str] = None
