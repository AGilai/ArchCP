import threading
import time
import random
from pymongo import MongoClient

# Imports
from provisioning_service.core.config import settings
from provisioning_service.core.domain_models import ProvisioningRequest
from provisioning_service.adapters.sqs_consumer import SQSConsumer
from provisioning_service.adapters.mqtt_publisher import MqttPublisher
from provisioning_service.adapters.repositories import AgentRepository, RuleRepository, SegmentStateRepository
from provisioning_service.logic.worker import ProvisioningOrchestrator

# --- 1. Wiring ---
client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

agent_repo = AgentRepository(db)
rule_repo = RuleRepository(db)
seg_repo = SegmentStateRepository(db)
publisher = MqttPublisher()

orchestrator = ProvisioningOrchestrator(
    agent_repo, rule_repo, seg_repo, publisher, settings.TENANT_ID
)

# --- 2. The Threads ---

def start_sqs_listener():
    """Real Input: Listens for Agent Bootstraps"""
    consumer = SQSConsumer()
    
    def callback(raw_data):
        try:
            req = ProvisioningRequest(**raw_data)
            orchestrator.process_bootstrap(req)
        except Exception as e:
            print(f"[SQS Error] {e}")

    print("[Thread-1] SQS Consumer Started (Bootstrap Listener)")
    consumer.start_listening(callback)

def start_simulation_loop():
    """
    Simulated Input: ACTS AS THE ADMIN CONSOLE.
    1. Picks a segment.
    2. Writes a new version to the DB (The "Command").
    3. Notifies the Orchestrator (The "Event").
    """
    print("[Thread-2] Chaos Simulator Started (Acting as Admin)")
    while True:
        time.sleep(5) 
        try:
            # A. Pick a random segment
            all_segments = rule_repo.get_all_target_segments()
            if all_segments:
                target_segment = random.choice(all_segments)
                
                # B. ADMIN ACTION: Create/Increment the version in the DB
                # This simulates the Admin clicking "Publish" in the UI
                new_version = seg_repo.increment_version(target_segment)
                print(f"[Simulator] Admin published v{new_version} for {target_segment}")
                
                # C. EVENT TRIGGER: Notify the Orchestrator
                orchestrator.process_new_version_notification(target_segment, new_version)
                
        except Exception as e:
            print(f"[Sim Error] {e}")

if __name__ == "__main__":
    if settings.ENABLE_SIMULATOR:
        sim_thread = threading.Thread(target=start_simulation_loop, daemon=True)
        sim_thread.start()
    
    start_sqs_listener()