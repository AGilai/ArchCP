import paho.mqtt.client as mqtt
import json

class MqttPublisher:
    def __init__(self):
        # FIX: Explicitly use VERSION2
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "backend-worker")
        self.client.connect("localhost", 1883)
        self.client.loop_start()

    def publish_policy(self, tenant_id: str, agent_id: str, payload: dict):
        topic = f"sase/{tenant_id}/node/{agent_id}"
        self.client.publish(topic, json.dumps(payload), qos=1)
        print(f"[Worker] Published to {topic}")