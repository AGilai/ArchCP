from provisioning_service.adapters.mongo_repository import MongoRepository
from provisioning_service.adapters.sqs_consumer import SQSConsumer
from provisioning_service.adapters.mqtt_publisher import MqttPublisher
from provisioning_service.core.domain_models import ProvisioningRequest, PolicyResponse

# Initialize Adapters
repo = MongoRepository()
mq = MqttPublisher()
sqs = SQSConsumer()

def process_provisioning(raw_data: dict):
    # 1. Parse Input
    req = ProvisioningRequest(**raw_data)
    print(f"\n[Worker] Processing: {req.agent_id}")
    print(f"         Groups: {req.context.groups}")

    # 2. Logic: Mongo Lookup
    assigned_segments = repo.get_segments_for_user(req.context)

    # 3. Create Response
    resp = PolicyResponse(
        status="SUCCESS",
        assigned_segments=assigned_segments,
        policy_version="v1.0.55",
        download_url=f"https://cdn.cp.com/{req.tenant_id}/policy.bin"
    )

    # 4. Publish to Agent
    mq.publish_policy(req.tenant_id, req.agent_id, resp.model_dump())

if __name__ == "__main__":
    sqs.start_listening(process_provisioning)