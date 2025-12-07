# User-Aware Policy Enforcement System (POC)

This Proof of Concept (POC) demonstrates a **Cloud-Native, Event-Driven Policy Distribution System** designed for massive scale. It implements a decoupled architecture separating the **Control Plane** (Management & Simulation) from the **Data Plane** (Enforcement Agents).

## 🏗 System Architecture

The system is composed of four decoupled microservices communicating via asynchronous protocols (MQTT & SQS).



| Component | Role | Technology |
| :--- | :--- | :--- |
| **Agent (Data Plane)** | Simulates an endpoint device. Manages local state (files), connects to the cloud, and enforces policies. | Python (FastAPI), Paho-MQTT, Local File Locking |
| **Bridge (IoT Rule Engine)** | Ingests MQTT signals from agents and routes them to the backend queue (decoupling). | Python, Paho-MQTT, Boto3 |
| **Worker (Control Plane)** | The "Brain". Processes requests, talks to the DB, compiles policies, and triggers push notifications. | Python, MongoDB (Pymongo), SQS |
| **Simulator (Admin Console)** | Runs inside the Worker. Randomly generates policy updates to simulate Admin activity. | Python Threading |
| **Infrastructure** | Provides the message bus and storage. | Docker (Mosquitto, MongoDB, LocalStack) |

---

## 🚀 1. Prerequisites

Ensure you have the following installed:
* **Docker & Docker Compose**
* **Python 3.9+**

---

## 🛠 2. Installation & Setup

### Step A: Initialize the Environment
Run the setup script to create the folder structure, virtual environment, and empty files.

```bash
# 1. Create directory structure (if not already done)
./setup_poc.sh 

# 2. Create and activate Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python Dependencies
pip install -r requirements.txt