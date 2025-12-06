from fastapi import FastAPI
import paho.mqtt.client as mqtt
import json
import asyncio
from identity_provider import IdentityProvider

# --- Initialize Identity ---
# This will lock "client_1" on first run, "client_2" on second, etc.
id_provider = IdentityProvider()
my_identity = id_provider.acquire_identity()

AGENT_ID = my_identity["client_id"]
TENANT_ID = my_identity["tenant_id"]
MY_GROUPS = my_identity["groups"]
MY_TOPIC = f"sase/{TENANT_ID}/node/{AGENT_ID}"

app = FastAPI()

# --- MQTT Setup with Persistence ---
# clean_session=False is CRITICAL. It tells the broker:
# "If I disconnect, keep my messages in a queue until I come back."
mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, 
    client_id=AGENT_ID, 
    clean_session=False 
)

def on_connect(client, userdata, flags, reason_code, properties):
    # FIX: Access session_present as an attribute, not a dictionary key
    session_present = flags.session_present
    print(f"[{AGENT_ID}] Connected! (Session Present: {session_present})")
    
    # Subscribe with QoS 1 (Guaranteed Delivery)
    client.subscribe(MY_TOPIC, qos=1)
    
    # Only bootstrap if we are new or lost session (optional logic)
    # For this POC, we send bootstrap every time to force a refresh
    payload = {
        "request_id": "req-init",
        "agent_id": AGENT_ID,
        "tenant_id": TENANT_ID,
        "context": {
            "user_id": f"user-of-{AGENT_ID}",
            "groups": MY_GROUPS,
            "location": "Tel-Aviv"
        }
    }
    client.publish("client_requests", json.dumps(payload))
    print(f"[{AGENT_ID}] Sent Bootstrap -> 'client_requests'")

def on_message(client, userdata, msg):
    print(f"\n✨ [{AGENT_ID}] MESSAGE RECEIVED ✨")
    print(f"   Topic: {msg.topic}")
    try:
        data = json.loads(msg.payload.decode())
        print(f"   Payload: {json.dumps(data, indent=2)}")
        
        # Update local disk state
        if "assigned_segments" in data:
            id_provider.update_segments(data["assigned_segments"])
            
    except:
        print(f"   Payload: {msg.payload.decode()}")
    print("-" * 40)

@app.on_event("startup")
async def startup():
    print(f"\n=== AGENT STARTED: {AGENT_ID} ===")
    print(f"   Identity loaded from disk.")
    print(f"   Groups: {MY_GROUPS}")
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Broker connection failed: {e}")