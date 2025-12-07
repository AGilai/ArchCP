import paho.mqtt.client as mqtt
import json
from ..core.config import settings
from provisioning_service.core.logger import get_logger

logger = get_logger("MqttPublisher")

class MqttPublisher:
    def __init__(self):
        # Initialize the client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "backend-worker")
        self.client.connect(settings.MQTT_HOST, settings.MQTT_PORT)
        self.client.loop_start()

    def send_private_response(self, agent_id: str, tenant_id: str, payload: dict):
        """Sends a message to a specific agent's private topic."""
        topic = f"sase/{tenant_id}/node/{agent_id}"
        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Sent Private Response to {topic}")

    def broadcast_update(self, tenant_id: str, segment_id: str, payload: dict):
        """Broadcasts a message to all agents listening on a segment topic."""
        topic = f"sase/{tenant_id}/segment/{segment_id}"
        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Broadcasted Update to {topic}")