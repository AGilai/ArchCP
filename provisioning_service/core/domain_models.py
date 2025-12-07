from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field

# --- Sub-Models ---
class UserContext(BaseModel):
    user_id: str
    groups: List[str]
    location: str

# --- SQS Message Types ---

class BootstrapPayload(BaseModel):
    request_id: str
    agent_id: str
    context: UserContext

class UpdateTriggerPayload(BaseModel):
    segment_id: str
    reason: str = "SIMULATED_ADMIN_ACTION"

# --- The Envelope (Polymorphic) ---
class SQSMessage(BaseModel):
    type: Literal["BOOTSTRAP", "UPDATE_TRIGGER"]
    tenant_id: str
    payload: Union[BootstrapPayload, UpdateTriggerPayload]

# --- Response Model (MQTT) ---
class PolicyResponse(BaseModel):
    status: str
    assigned_segments: List[str]
    segment_topics: List[str]
    segment_versions: Dict[str, int]
    download_url: str