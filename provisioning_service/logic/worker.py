from typing import List
from ..core.domain_models import BootstrapRequest, ProvisioningManifest, UserContext
from ..core.interfaces import IPolicyRepository, IMessageBroker

class ProvisioningWorker:
    def __init__(self, repo: IPolicyRepository, broker: IMessageBroker):
        self.repo = repo
        self.broker = broker

    def process_bootstrap_request(self, tenant_id: str, request: BootstrapRequest):
        print(f"\n[Worker] Processing Bootstrap for Agent: {request.agent_id}...")

        # Step 1: Context Extraction (Simulating JWT Validation)
        # In production, we would verify the JWT signature here.
        user_context = request.mock_decoded_context
        if not user_context:
            raise ValueError("Invalid Context")
        
        print(f"   > User Context Identified: {user_context.groups} in {user_context.location}")

        # Step 2: Segmentation Logic (Phase 2 of HLD)
        # Calculate which segments this user belongs to based on rules
        active_segments = self._evaluate_segments(user_context)
        print(f"   > Calculated Segments: {active_segments}")

        # Step 3: Fetch Artifacts (Phase 3 of HLD - Manifest Generation)
        # Get the specific S3 URLs for these segments
        artifacts = self.repo.get_latest_artifacts(active_segments)
        
        # Step 4: Construct Manifest
        # Define which topics the agent should listen to
        subscriptions = [f"sase/{tenant_id}/policy/segment/{seg}" for seg in active_segments]
        subscriptions.append(f"sase/{tenant_id}/node/{request.agent_id}") # Targeted channel

        manifest = ProvisioningManifest(
            assigned_segments=active_segments,
            artifacts=artifacts,
            mqtt_subscriptions=subscriptions
        )

        # Step 5: Signaling (Push to Agent)
        self.broker.publish_manifest(tenant_id, request.agent_id, manifest.model_dump())
        print("[Worker] Process Complete.\n")

    def _evaluate_segments(self, context: UserContext) -> List[str]:
        """Matches user attributes against repository rules."""
        rules = self.repo.get_segmentation_rules()
        assigned = []
        
        # Always add default/global segment
        assigned.append("global-segment")

        for rule in rules:
            match_group = True
            match_loc = True

            if rule.required_group and rule.required_group not in context.groups:
                match_group = False
            
            if rule.required_location and rule.required_location != context.location:
                match_loc = False

            if match_group and match_loc:
                assigned.append(rule.target_segment_id)
        
        return list(set(assigned))