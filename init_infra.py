import boto3
import pymongo
import time

def init_aws():
    print("[INIT] Connecting to LocalStack SQS...")
    sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
    try:
        sqs.create_queue(QueueName='provisioning-queue')
        print("   ✅ SQS Queue 'provisioning-queue' created")
    except Exception as e:
        print(f"   ⚠️ SQS Error (might already exist): {e}")

def init_mongo():
    print("[INIT] Connecting to MongoDB...")
    client = pymongo.MongoClient("mongodb://admin:password@localhost:27017/")
    db = client["sase_db"]
    
    # 1. Clean old rules
    db["segment_rules"].delete_many({})
    
    # 2. Seed new rules (Group -> Segment Mapping)
    rules = [
        {"required_group": "finance", "target_segment": "seg-finance-confidential"},
        {"required_group": "hr",      "target_segment": "seg-hr-data-privacy"},
        {"required_group": "dev",     "target_segment": "seg-developers-prod-access"},
        {"required_group": "sales",   "target_segment": "seg-sales-crm"},
        {"required_group": "it",      "target_segment": "seg-admin-root"}
    ]
    
    db["segment_rules"].insert_many(rules)
    print(f"   ✅ MongoDB seeded with {len(rules)} rules.")

if __name__ == "__main__":
    init_aws()
    init_mongo()