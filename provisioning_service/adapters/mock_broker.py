import json
from ..core.interfaces import IMessageBroker

class ConsoleBroker(IMessageBroker):
    def publish_manifest(self, tenant_id: str, agent_id: str, manifest: dict):
        topic = f"sase/{tenant_id}/node/{agent_id}"
        print("--- [MQTT SIMULATION] PUBLISH ---")
        print(f"TOPIC: {topic}")
        print(f"PAYLOAD: {json.dumps(manifest, indent=2)}")
        print("---------------------------------")