import boto3
import json
from ..core.config import settings

class SQSConsumer:
    def __init__(self):
        self.sqs = boto3.client(
            'sqs', 
            endpoint_url=settings.SQS_ENDPOINT_URL, 
            region_name=settings.AWS_REGION
        )
        self.queue_url = settings.SQS_QUEUE_URL
        
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