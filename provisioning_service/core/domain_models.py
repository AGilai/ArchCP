from typing import List, Optional
from pydantic import BaseModel

# Input: Context coming from the Agent
class UserContext(BaseModel):
    user_id: str
    groups: List[str]
    location: str

# Message: The payload moving from SQS -> Worker
class ProvisioningRequest(BaseModel):
    request_id: str
    agent_id: str
    tenant_id: str
    context: UserContext

# Output: The payload moving from Worker -> Agent
class PolicyResponse(BaseModel):
    status: str
    assigned_segments: List[str]
    policy_version: str
    download_url: str