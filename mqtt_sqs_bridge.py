import paho.mqtt.client as mqtt
import boto3
import json

MQTT_TOPIC = "client_requests"
SQS_URL = "http://localhost:4566/000000000000/provisioning-queue"

sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')

def on_connect(client, userdata, flags, reason_code, properties):
    # Note: Callback signature changed in v2 (added properties)
    print(f"[*] Bridge Connected. Subscribing to '{MQTT_TOPIC}'...")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print(f"[->] Received MQTT: {payload}")
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=payload)
        print(f"[<-] Forwarded to SQS")
    except Exception as e:
        print(f"[!] Bridge Error: {e}")

if __name__ == "__main__":
    # FIX: Explicitly use VERSION2
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "bridge-service")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect("localhost", 1883, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("Bridge stopped.")