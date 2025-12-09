import sys
import os

from provisioning_service.core.logger import get_logger
from provisioning_service.infra_utils import set_tab_title

# Ensure we can import modules if running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient
from provisioning_service.core.config import settings
from provisioning_service.core.domain_models import SQSMessage
from provisioning_service.adapters.sqs_consumer import SQSConsumer
from provisioning_service.adapters.mqtt_publisher import MqttPublisher
from provisioning_service.adapters.repositories import AgentRepository, RuleRepository, SegmentStateRepository
from provisioning_service.logic.worker import ProvisioningOrchestrator

logger = get_logger("ProvisioningService")

# --- Wiring Dependencies ---
def bootstrap_app():
    # 1. Infrastructure
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    
    # 2. Adapters
    agent_repo = AgentRepository(db)
    rule_repo = RuleRepository(db)
    seg_repo = SegmentStateRepository(db)
    publisher = MqttPublisher()
    
    # 3. Core Logic (Orchestrator)
    return ProvisioningOrchestrator(
        agent_repo=agent_repo,
        rule_repo=rule_repo,
        seg_repo=seg_repo,
        publisher=publisher
    )

# --- Message Loop ---
def run():
    set_tab_title("Provisioning Service")
    logger.info("Initializing Provisioning Worker...")
    orchestrator = bootstrap_app()
    consumer = SQSConsumer()

    def process_message(raw_data):
        try:
            # Parse Envelope
            msg = SQSMessage(**raw_data)
            
            # Route to Logic
            if msg.type == "BOOTSTRAP":
                orchestrator.handle_bootstrap(msg.tenant_id, msg.payload)
                
            elif msg.type == "UPDATE_TRIGGER":
                orchestrator.handle_update_trigger(msg.tenant_id, msg.payload)
                
        except Exception as e:
            print(f"[Worker Error] Processing Failed: {e}")

    print("[Service] 🚀 Worker Started. Listening to SQS...")
    consumer.start_listening(process_message)

if __name__ == "__main__":
    run()