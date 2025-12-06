import boto3
import json

class SQSConsumer:
    def __init__(self):
        self.sqs = boto3.client('sqs', endpoint_url='http://localhost:4566', region_name='us-east-1')
        self.queue_url = "http://localhost:4566/000000000000/provisioning-queue"

    def start_listening(self, callback):
        print("[Worker] Listening for SQS messages...")
        while True:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=5
            )
            if 'Messages' in response:
                for msg in response['Messages']:
                    try:
                        body = json.loads(msg['Body'])
                        callback(body)
                        self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=msg['ReceiptHandle'])
                    except Exception as e:
                        print(f"[!] Error: {e}")