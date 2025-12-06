from typing import List
from ..core.interfaces import IPolicyRepository
from ..core.domain_models import SegmentRule, PolicyArtifact

class InMemoryRepository(IPolicyRepository):
    def __init__(self):
        # Simulating Database Rules
        self.rules = [
            SegmentRule(rule_name="Finance Dept", target_segment_id="segment-finance", required_group="finance-group"),
            SegmentRule(rule_name="NYC Office", target_segment_id="segment-nyc", required_location="NYC"),
            SegmentRule(rule_name="Devs", target_segment_id="segment-dev", required_group="developers"),
        ]

    def get_segmentation_rules(self) -> List[SegmentRule]:
        return self.rules

    def get_latest_artifacts(self, segment_ids: List[str]) -> List[PolicyArtifact]:
        artifacts = []
        for seg in segment_ids:
            # Simulating S3 paths and CloudFront URLs
            artifacts.append(PolicyArtifact(
                artifact_type="rules_wasm",
                version="v56",
                segment_id=seg,
                download_url=f"https://cdn.sase.checkpoint.com/{seg}/v56/policy.wasm",
                sha256="a1b2c3d4e5..."
            ))
        return artifacts