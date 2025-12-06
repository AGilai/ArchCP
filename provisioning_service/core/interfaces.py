from abc import ABC, abstractmethod
from typing import List
from .domain_models import SegmentRule, PolicyArtifact

class IPolicyRepository(ABC):
    """Interface for fetching Rules and Policy Metadata (Simulating MongoDB/DynamoDB)."""
    
    @abstractmethod
    def get_segmentation_rules(self) -> List[SegmentRule]:
        pass

    @abstractmethod
    def get_latest_artifacts(self, segment_ids: List[str]) -> List[PolicyArtifact]:
        pass

class IMessageBroker(ABC):
    """Interface for Signaling (Simulating AWS IoT Core)."""
    
    @abstractmethod
    def publish_manifest(self, tenant_id: str, agent_id: str, manifest: dict):
        pass