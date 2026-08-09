"""Dedicated, light-weight Pydantic schemas for Dialogue turn generation and verification."""

from typing import Optional, Literal
from pydantic import BaseModel, Field

class IntakeAnalysis(BaseModel):
    target_id: str = Field(description="ID of the panelist whose argument you are contesting (e.g. p1, p2)")
    flawed_claim: str = Field(description="Summarize what they said that is incomplete or flawed in 1 sentence")
    your_counter_angle: str = Field(description="Why their view is flawed from your philosophical role")

class DialogueTurn(BaseModel):
    target_id: str = Field(description="ID of target panelist being addressed (e.g. p1, p2)")
    claim: str = Field(description="Your core assertion in 1-2 sharp sentences")
    evidence: str = Field(description="Supporting principle, logical reason, or analogy")
    challenge: str = Field(description="Direct objection to target_id's stance")
    question: str = Field(description="Probing question for the panel")

class TargetedRepairRequest(BaseModel):
    corrected_target_id: str = Field(description="Corrected panelist ID from the valid options (e.g. p1, p2, p3)")
