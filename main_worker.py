import threading
import time
import random
import json
import paho.mqtt.client as mqtt
from pymongo import MongoClient, ReturnDocument
from provisioning_service.adapters.sqs_consumer import SQSConsumer
from provisioning_service.core.domain_models import ProvisioningRequest, PolicyResponse

# --- Configuration ---
MONGO_URI = "mongodb://admin:password@localhost:27017/"
TENANT_ID = "tenant-cp"

# --- Infrastructure Adapters (Inline for simplicity) ---
class MongoManager:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client["sase_db"]

    def get_segments_for_user(self, groups):
        """Logic: Map Groups -> Segments"""
        segments = ["seg-global"] # Everyone gets global
        rules_col = self.db["segment_rules"]
        for group in groups:
            rule = rules_col.find_one({"required_group": group})
            if rule:
                segments.append(rule["target_segment"])
        return list(set(segments))

    def register_agent(self, agent_id, segments):
        """Req 1: Write Agent State to Mongo"""
        self.db["agents_state"].update_one(
            {"agent_id": agent_id},
            {"$set": {
                "agent_id": agent_id,
                "segments": segments,
                "last_seen": time.time(),
                "status": "ONLINE"
            }},
            upsert=True
        )
        print(f"[DB] Registered Agent {agent_id} with segments: {segments}")

    def get_all_active_segments(self):
        """Find all unique segments currently used by rules"""
        return self.db["segment_rules"].distinct("target_segment")

    def increment_segment_version(self, segment_id):
        """Req 4: Increment version for a segment"""
        # We store segment state in a 'segments_state' collection
        doc = self.db["segments_state"].find_one_and_update(
            {"segment_id": segment_id},
            {"$inc": {"version_counter": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return doc["version_counter"]
    
    def get_current_versions(self, segments):
        """Fetch the current version number for a list of segments."""
        versions = {}
        # Get all docs matching our segments
        cursor = self.db["segments_state"].find({"segment_id": {"$in": segments}})
        
        # Create a lookup map
        found_map = {doc["segment_id"]: doc["version_counter"] for doc in cursor}
        
        for seg in segments:
            # Default to version 0 if never updated
            versions[seg] = found_map.get(seg, 0)
            
        return versions

class BackendPublisher:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "backend-simulator")
        self.client.connect("localhost", 1883)
        self.client.loop_start()

    def send_private_response(self, agent_id, payload):
        """Send Bootstrap Response (Private)"""
        topic = f"sase/{TENANT_ID}/node/{agent_id}"
        self.client.publish(topic, json.dumps(payload), qos=1)
        print(f"[Onboarding] Sent Policy to {agent_id}")

    def broadcast_segment_update(self, segment_id, version, payload):
        """Req 3: Send Payload to Segment Topic"""
        topic = f"sase/{TENANT_ID}/segment/{segment_id}"
        self.client.publish(topic, json.dumps(payload), qos=1)
        print(f"[Simulator] 📡 Broadcast update v{version} to '{topic}'")

# --- Logic Controllers ---

# 1. The Reactive Thread (Onboarding)
def handle_bootstrap_requests(mongo: MongoManager, pub: BackendPublisher):
    consumer = SQSConsumer()
    
    def callback(raw_data):
        try:
            req = ProvisioningRequest(**raw_data)
            print(f"\n[Onboarding] Processing: {req.agent_id} ({req.context.groups})")

            # A. Calculate Segments
            segments = mongo.get_segments_for_user(req.context.groups)
            
            # B. Persist Agent State
            mongo.register_agent(req.agent_id, segments)

            # C. Fetch Current Versions (NEW STEP)
            versions_map = mongo.get_current_versions(segments)
            
            # D. Generate Response
            segment_topics = [f"sase/{TENANT_ID}/segment/{seg}" for seg in segments]
            
            resp = PolicyResponse(
                status="SUCCESS",
                assigned_segments=segments,
                segment_topics=segment_topics,
                segment_versions=versions_map,  # <--- Populated Here
                download_url="http://cdn.sase.com/init.bin"
            )
            
            pub.send_private_response(req.agent_id, resp.model_dump())
            
        except Exception as e:
            print(f"[Onboarding Error] {e}")

    print("[Thread-1] Listening for Onboarding Requests...")
    consumer.start_listening(callback)

# 2. The Proactive Thread (Simulator)
def run_chaos_simulator(mongo: MongoManager, pub: BackendPublisher):
    print("[Thread-2] Simulator Started (Auto-Updating Segments)...")
    while True:
        time.sleep(5) # Req 4: Run every X seconds
        
        try:
            # A. Pick a random segment
            all_segments = mongo.get_all_active_segments()
            if not all_segments:
                continue
                
            target_segment = random.choice(all_segments)
            
            # B. Increment Version
            new_ver = mongo.increment_segment_version(target_segment)
            
            # C. Req 3: Payload prefixed as segment_ver_number
            payload = {
                "type": "SEGMENT_UPDATE",
                "segment": target_segment,
                "version": new_ver,
                "payload_content": f"{target_segment}_ver_{new_ver}_security_rules_blob"
            }
            
            # D. Broadcast
            pub.broadcast_segment_update(target_segment, new_ver, payload)
            
        except Exception as e:
            print(f"[Simulator Error] {e}")

# --- Main Entry Point ---
if __name__ == "__main__":
    mongo = MongoManager()
    pub = BackendPublisher()
    
    # Start Simulator in background thread
    sim_thread = threading.Thread(target=run_chaos_simulator, args=(mongo, pub))
    sim_thread.daemon = True
    sim_thread.start()
    
    # Run Consumer in main thread
    handle_bootstrap_requests(mongo, pub)