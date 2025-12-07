import json
from ..core.domain_models import ProvisioningRequest, PolicyResponse
from ..core.entities import AgentStateEntity
from ..adapters.repositories import AgentRepository, RuleRepository, SegmentStateRepository
from ..adapters.mqtt_publisher import MqttPublisher

class ProvisioningOrchestrator:
    """
    The CORE LOGIC of the Distribution Plane.
    """
    def __init__(self, 
                 agent_repo: AgentRepository, 
                 rule_repo: RuleRepository, 
                 seg_repo: SegmentStateRepository,
                 publisher: MqttPublisher,
                 tenant_id: str):
        self.agent_repo = agent_repo
        self.rule_repo = rule_repo
        self.seg_repo = seg_repo
        self.publisher = publisher
        self.tenant_id = tenant_id

    def process_bootstrap(self, request: ProvisioningRequest):
        # ... (This method remains exactly the same as before) ...
        print(f"\n[Orchestrator] Handling Bootstrap for {request.agent_id}")
        
        assigned_segments = ["seg-global"]
        for group in request.context.groups:
            rule = self.rule_repo.find_rule_for_group(group)
            if rule:
                assigned_segments.append(rule.target_segment)
        
        assigned_segments = list(set(assigned_segments))

        agent_entity = AgentStateEntity(
            agent_id=request.agent_id,
            tenant_id=self.tenant_id,
            assigned_segments=assigned_segments,
            status="ONLINE"
        )
        self.agent_repo.upsert_agent(agent_entity)

        versions_map = self.seg_repo.get_versions_map(assigned_segments)
        
        segment_topics = [f"sase/{self.tenant_id}/segment/{seg}" for seg in assigned_segments]
        
        response = PolicyResponse(
            status="SUCCESS",
            assigned_segments=assigned_segments,
            segment_topics=segment_topics,
            segment_versions=versions_map,
            download_url="http://cdn.sase.com/init.bin"
        )

        self.publisher.send_private_response(request.agent_id, self.tenant_id, response.model_dump())
        print(f"[Orchestrator] ✅ Sent Bootstrap Response to {request.agent_id}")

    def process_new_version_notification(self, segment_id: str, new_version: int):
        """
        Flow 2: React to a new version event.
        Logic: Create Payload -> Broadcast
        (Note: We do NOT increment the DB here. We assume the Admin/Simulator already did that.)
        """
        print(f"[Orchestrator] 🔔 Received Trigger: {segment_id} is now v{new_version}")

        # 1. Logic: Create the Update Payload
        # In a real system, we might fetch the specific policy blob from S3 here using the version
        payload = {
            "type": "SEGMENT_UPDATE",
            "segment": segment_id,
            "version": new_version,
            "payload_content": f"blob_{segment_id}_v{new_version}"
        }
        
        # 2. Signaling: Broadcast to Segment Topic
        self.publisher.broadcast_update(self.tenant_id, segment_id, payload)
        print(f"[Orchestrator] 📡 Broadcasted Update v{new_version} to {segment_id}")