from fastapi import FastAPI
import paho.mqtt.client as mqtt
import json
from identity_provider import IdentityProvider
from provisioning_service.core.logger import get_logger

logger = get_logger("AgentApp")

# --- Identity ---
id_provider = IdentityProvider()
my_identity = id_provider.acquire_identity()

AGENT_ID = my_identity["client_id"]
TENANT_ID = "tenant-cp"
MY_GROUPS = my_identity["groups"]
MY_PRIVATE_TOPIC = f"sase/{TENANT_ID}/node/{AGENT_ID}"

app = FastAPI()

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, 
    client_id=AGENT_ID, 
    clean_session=False 
)

def on_connect(client, userdata, flags, reason_code, properties):
    session_present = flags.session_present
    logger.info(f"[{AGENT_ID}] Connected! (Session Present: {session_present})")

    # 1. ALWAYS subscribe to private channel
    client.subscribe(MY_PRIVATE_TOPIC, qos=1)

    # 2. Check Local Disk for Segments
    saved_segments = id_provider.data.get("assigned_segments", [])
    
    if saved_segments:
        print(f"[{AGENT_ID}] Found {len(saved_segments)} segments on disk.")
        for seg in saved_segments:
            topic = f"sase/{TENANT_ID}/segment/{seg}"
            client.subscribe(topic, qos=1)
            logger.info(f"   ↪ Resubscribed to: {topic} (QoS 1)")

        logger.info(f"[{AGENT_ID}] Skipping Bootstrap (Using Cached Policy)")
        logger.info(f"[{AGENT_ID}] Waiting for queued messages...")

    else:
        # 3. No segments on disk? Bootstrap!
        payload = {
            "request_id": "init",
            "agent_id": AGENT_ID,
            "tenant_id": TENANT_ID,
            "context": {"user_id": "u1", "groups": MY_GROUPS, "location": "TLV"}
        }
        client.publish("client_requests", json.dumps(payload))
        logger.info(f"[{AGENT_ID}] Disk Empty -> Sent Bootstrap Request")

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode()
        data = json.loads(raw_payload)
        
        # CASE 1: Bootstrap Response (Private)
        if msg.topic == MY_PRIVATE_TOPIC:
            logger.info(f"[{AGENT_ID}] BOOTSTRAP RESPONSE ✨")

            if 'assigned_segments' in data:
                # Save to disk
                id_provider.update_segments(data['assigned_segments'])
            
            # Subscribe with Version Info
            topics = data.get("segment_topics", [])
            versions = data.get("segment_versions", {})
            
            for topic in topics:
                # Extract segment ID from topic (sase/tenant/segment/SEG_ID)
                seg_id = topic.split("/")[-1]
                ver = versions.get(seg_id, "?")
                download_url = data.get("download_url", "N/A")
                
                client.subscribe(topic, qos=1)
                logger.info(f"Subscribed to: {topic} (Current Version: v{ver}) | Download URL: {download_url})")

        # CASE 2: Segment Update
        elif "segment" in msg.topic:
            logger.info(f"[{AGENT_ID}] UPDATE from {msg.topic} | New Version: {data.get('version', 'unknown')}")

    except Exception as e:
        logger.error(f"Error parsing msg: {e}")

@app.on_event("startup")
async def startup():
    logger.info(f"=== AGENT {AGENT_ID} STARTING ===")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_start()
    except:
        print("Broker connection failed.")