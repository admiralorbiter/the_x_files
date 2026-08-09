from __future__ import annotations
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator
import uuid
import datetime

# --- Action Primitives (Agent Proposals) ---

ActionType = Literal[
    "observe",
    "move",
    "gather",
    "trade",
    "create_institution",
    "spawn_agent",
    "record_artifact",
    "speak"
]

class AgentAction(BaseModel):
    action_type: ActionType
    target_location: Optional[str] = None
    target_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_amount: int = 0
    institution_name: Optional[str] = None
    institution_charter: Optional[str] = None
    sub_agent_name: Optional[str] = None
    sub_agent_motive: Optional[str] = None
    artifact_title: Optional[str] = None
    artifact_content: Optional[str] = None
    message: Optional[str] = None
    rationale: str = Field(default="Reasoning for action", description="Internal reasoning for choosing this action")

    @field_validator('target_agent', 'target_location', mode='before')
    @classmethod
    def coerce_string_or_list(cls, v: Any) -> Optional[str]:
        if isinstance(v, list):
            return ", ".join(str(item) for item in v)
        if v is not None:
            return str(v)
        return None

    @field_validator('resource_amount', mode='before')
    @classmethod
    def coerce_int(cls, v: Any) -> int:
        if isinstance(v, list) and len(v) > 0:
            v = v[0]
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

class AgentTurnProposal(BaseModel):
    thoughts: str = Field(default="Reflecting on dialogue.", description="Agent's private thoughts and reflection on current situation")
    action: AgentAction

# --- Domain Event Schemas (Append-Only Event Store) ---

class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    tick: int
    event_type: str
    actor_id: str
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None

# --- Domain Models ---

class AgentState(BaseModel):
    agent_id: str
    name: str
    persona: str
    motive: str
    location: str
    resources: Dict[str, int] = Field(default_factory=dict)
    parent_agent_id: Optional[str] = None
    status: str = "active"

class Institution(BaseModel):
    institution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    creator_id: str
    charter: str
    members: List[str] = Field(default_factory=list)
    created_at_tick: int

class Artifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    author_id: str
    content: str
    created_at_tick: int

class LocationState(BaseModel):
    name: str
    description: str
    resources: Dict[str, int] = Field(default_factory=dict)
    connected_locations: List[str] = Field(default_factory=list)

class WorldState(BaseModel):
    run_id: str
    tick: int = 0
    locations: Dict[str, LocationState] = Field(default_factory=dict)
    agents: Dict[str, AgentState] = Field(default_factory=dict)
    institutions: Dict[str, Institution] = Field(default_factory=dict)
    artifacts: Dict[str, Artifact] = Field(default_factory=dict)
