#!/bin/bash

# Define the base directory
BASE_DIR="/Users/asafgilai/MyStuf/ArchCP"

# Create the directory structure
echo "Creating directories..."
mkdir -p "$BASE_DIR/provisioning_service/core"
mkdir -p "$BASE_DIR/provisioning_service/logic"
mkdir -p "$BASE_DIR/provisioning_service/adapters"

# Create the empty files
echo "Creating empty files..."
touch "$BASE_DIR/requirements.txt"
touch "$BASE_DIR/main.py"

# provisioning_service files
touch "$BASE_DIR/provisioning_service/__init__.py"

# Core layer
touch "$BASE_DIR/provisioning_service/core/__init__.py"
touch "$BASE_DIR/provisioning_service/core/domain_models.py"
touch "$BASE_DIR/provisioning_service/core/interfaces.py"

# Logic layer
touch "$BASE_DIR/provisioning_service/logic/__init__.py"
touch "$BASE_DIR/provisioning_service/logic/worker.py"

# Adapters layer
touch "$BASE_DIR/provisioning_service/adapters/__init__.py"
touch "$BASE_DIR/provisioning_service/adapters/mock_repository.py"
touch "$BASE_DIR/provisioning_service/adapters/mock_broker.py"

echo "Success! Structure created at: $BASE_DIR"
echo "You can now open this folder in your IDE and paste the content."