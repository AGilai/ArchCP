#!/bin/bash
BASE_DIR=$(pwd)

echo "📂 Creating Directory Structure in $BASE_DIR..."

# 1. Root files
touch docker-compose.yaml
touch mosquitto.conf
touch requirements.txt
touch init_infra.py
touch mqtt_sqs_bridge.py
touch agent_app.py
touch main_worker.py

# 2. The Backend Service Structure (The "Enterprise" Component)
mkdir -p provisioning_service/core
mkdir -p provisioning_service/adapters
mkdir -p provisioning_service/logic

touch provisioning_service/__init__.py
touch provisioning_service/core/__init__.py
touch provisioning_service/core/domain_models.py
touch provisioning_service/adapters/__init__.py
touch provisioning_service/adapters/mongo_repository.py
touch provisioning_service/adapters/sqs_consumer.py
touch provisioning_service/adapters/mqtt_publisher.py

echo "✅ Structure created successfully!"