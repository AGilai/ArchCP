from ..core.domain_models import BootstrapPayload, UpdateTriggerPayload, PolicyResponse
from ..core.entities import AgentStateEntity
from ..adapters.repositories import AgentRepository, RuleRepository, SegmentStateRepository
from ..adapters.mqtt_publisher import MqttPublisher
from provisioning_service.core.logger import get_logger

logger = get_logger("Orchestrator")

class ProvisioningOrchestrator:
    def __init__(self, agent_repo, rule_repo, seg_repo, publisher):
        self.agent_repo = agent_repo
        self.rule_repo = rule_repo
        self.seg_repo = seg_repo
        self.publisher = publisher

    def handle_bootstrap(self, tenant_id: str, payload: BootstrapPayload):
        logger.info(f"Processing Bootstrap for {payload.agent_id}")

        # 1. Logic
        # assigned_segments = ["seg-global"]
        assigned_segments = []
        for group in payload.context.groups:
            rule = self.rule_repo.find_rule_for_group(group)
            if rule:
                assigned_segments.append(rule.target_segment)
        
        assigned_segments = list(set(assigned_segments))

        # 2. Persist
        agent_entity = AgentStateEntity(
            agent_id=payload.agent_id,
            tenant_id=tenant_id,
            assigned_segments=assigned_segments
        )
        self.agent_repo.upsert_agent(agent_entity)

        # 3. Fetch Versions
        versions = self.seg_repo.get_versions_map(assigned_segments)

        # 4. Response
        topics = [f"sase/{tenant_id}/segment/{seg}" for seg in assigned_segments]
        resp = PolicyResponse(
            status="SUCCESS",
            assigned_segments=assigned_segments,
            segment_topics=topics,
            segment_versions=versions,
            download_url="http://cdn.sase.com/init.bin"
        )
        
        self.publisher.send_private_response(payload.agent_id, tenant_id, resp.model_dump())
        logger.info("Sent Bootstrap Response")

    def handle_update_trigger(self, tenant_id: str, payload: UpdateTriggerPayload):
        logger.info(f"Processing Update Trigger for {payload.segment_id}")
        
        # 1. Logic: Increment Version in DB
        new_version = self.seg_repo.increment_version(payload.segment_id)
        
        # 2. Logic: Create Notification Payload
        notify_payload = {
            "type": "SEGMENT_UPDATE",
            "segment": payload.segment_id,
            "version": new_version,
            "payload_content": f"blob_{payload.segment_id}_v{new_version}"
        }
        
        # 3. Broadcast
        self.publisher.broadcast_update(tenant_id, payload.segment_id, notify_payload)
        logger.info(f"Broadcasted v{new_version} for {payload.segment_id}")