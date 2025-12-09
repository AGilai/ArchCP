import paho.mqtt.client as mqtt
import boto3
import json
import time
import random
import threading
from pymongo import MongoClient

# Use our Clean Architecture imports
from provisioning_service.core.config import settings
from provisioning_service.adapters.repositories import RuleRepository

from provisioning_service.core.logger import get_logger
from provisioning_service.infra_utils import set_tab_title

# Initialize Logger
logger = get_logger("BridgeService")

# --- Configuration ---
MQTT_TOPIC = "client_requests"
SQS_URL = settings.SQS_QUEUE_URL
TENANT_ID = settings.TENANT_ID

# Initialize Infrastructure
sqs = boto3.client('sqs', endpoint_url=settings.SQS_ENDPOINT_URL, region_name=settings.AWS_REGION)
mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client[settings.DB_NAME]
rule_repo = RuleRepository(db)

# --- 1. MQTT Bridge Logic ---
def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"Connected. Subscribing to '{MQTT_TOPIC}'...")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """Handle Agent Bootstrap Requests"""
    try:
        raw_payload = json.loads(msg.payload.decode())
        logger.info(f"Received Bootstrap Request from {raw_payload.get('agent_id')}")
        
        envelope = {
            "type": "BOOTSTRAP",
            "tenant_id": TENANT_ID,
            "payload": {
                "request_id": raw_payload.get("request_id"),
                "agent_id": raw_payload.get("agent_id"),
                "context": raw_payload.get("context")
            }
        }
        
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(envelope))
        logger.info("Forwarded BOOTSTRAP to SQS")

    except Exception as e:
        logger.error(f"Bridge Error - {e}")

# --- 2. Simulator Logic (Dynamic) ---
def run_simulator_loop():
    """Simulates Admin clicking 'Update Policy' in the UI"""
    logger.info("Started Admin Simulation Loop...")
    
    while True:
        time.sleep(5) # Every 5 seconds
        
        try:
            # FIX: Fetch 'Live' segments from DB instead of hardcoding
            # This ensures we only simulate updates for segments that actually exist.
            active_segments = rule_repo.get_all_target_segments()
            
            if not active_segments:
                logger.warning("[No segments found in DB. Waiting...")
                continue

            target = random.choice(active_segments)
            
            envelope = {
                "type": "UPDATE_TRIGGER",
                "tenant_id": TENANT_ID,
                "payload": {
                    "segment_id": target,
                    "reason": "Scheduled Security Update"
                }
            }
            
            sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(envelope))
            logger.info(f"Triggered UPDATE for {target} -> SQS")
            
        except Exception as e:
            logger.error(f"[Simulator Error] {e}")

# --- Main Entry ---
if __name__ == "__main__":
    # Start Simulator Thread
    set_tab_title("Bridge & Simulator")

    sim_thread = threading.Thread(target=run_simulator_loop, daemon=True)
    sim_thread.start()

    # Start MQTT Bridge (Blocking)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "bridge-service")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
    client.loop_forever()