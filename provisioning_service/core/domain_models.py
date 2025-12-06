from typing import List, Dict, Optional
from pydantic import BaseModel

class UserContext(BaseModel):
    user_id: str
    groups: List[str]
    location: str

class ProvisioningRequest(BaseModel):
    request_id: str
    agent_id: str
    tenant_id: str
    context: UserContext

class PolicyResponse(BaseModel):
    status: str
    assigned_segments: List[str]
    segment_topics: List[str]
    segment_versions: Dict[str, int]
    download_url: str