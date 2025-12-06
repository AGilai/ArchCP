from fastapi import FastAPI
import paho.mqtt.client as mqtt
import json
from identity_provider import IdentityProvider

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
    # Fix for Paho v2 flag access
    session_present = flags.session_present
    print(f"[{AGENT_ID}] Connected! (Session Present: {session_present})")
    
    # 1. ALWAYS subscribe to private channel
    client.subscribe(MY_PRIVATE_TOPIC, qos=1)

    # 2. Check Local Disk for Segments
    saved_segments = id_provider.data.get("assigned_segments", [])
    
    if saved_segments:
        print(f"[{AGENT_ID}] 💾 Found {len(saved_segments)} segments on disk.")
        for seg in saved_segments:
            topic = f"sase/{TENANT_ID}/segment/{seg}"
            client.subscribe(topic, qos=1)
            print(f"   ↪ Resubscribed to: {topic} (QoS 1)")
        
        print(f"[{AGENT_ID}] Skipping Bootstrap (Using Cached Policy)")
        print(f"[{AGENT_ID}] Waiting for queued messages...")
        
    else:
        # 3. No segments on disk? Bootstrap!
        payload = {
            "request_id": "init",
            "agent_id": AGENT_ID,
            "tenant_id": TENANT_ID,
            "context": {"user_id": "u1", "groups": MY_GROUPS, "location": "TLV"}
        }
        client.publish("client_requests", json.dumps(payload))
        print(f"[{AGENT_ID}] 🆕 Disk Empty -> Sent Bootstrap Request")

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode()
        data = json.loads(raw_payload)
        
        # CASE 1: Bootstrap Response (Private)
        if msg.topic == MY_PRIVATE_TOPIC:
            print(f"\n [{AGENT_ID}] BOOTSTRAP RESPONSE RECEIVED ✨")
            
            if 'assigned_segments' in data:
                print(f"   Segments: {data['assigned_segments']}")
                
                # Show the versions we just got
                versions = data.get('segment_versions', {})
                print(f"   Current Versions: {json.dumps(versions, indent=4)}")
                
                id_provider.update_segments(data['assigned_segments'])
                
            # Subscribe to new topics
            topics = data.get("segment_topics", [])
            for topic in topics:
                client.subscribe(topic, qos=1)
                print(f"   Subscribed to: {topic}")

        # CASE 2: Segment Update
        elif "segment" in msg.topic:
            print(f"\n [{AGENT_ID}] UPDATE from {msg.topic}")
            print(f"   Version: {data.get('version', 'unknown')}")

    except Exception as e:
        print(f"Error parsing msg: {e}")

@app.on_event("startup")
async def startup():
    print(f"\n=== AGENT {AGENT_ID} STARTING ===")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_start()
    except:
        print("Broker connection failed.")