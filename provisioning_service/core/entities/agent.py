from typing import List
import time
from pydantic import Field
from .base import BaseEntity

class AgentStateEntity(BaseEntity):
    agent_id: str
    tenant_id: str
    assigned_segments: List[str]
    last_seen: float = Field(default_factory=time.time)
    status: str = "ONLINE"