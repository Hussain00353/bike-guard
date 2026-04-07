import json
import boto3
from datetime import datetime, timezone

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bike-guard-data')

def lambda_handler(event, context):
    """
    This function runs automatically every time
    a message arrives in the SQS queue.
    It saves the sensor data to DynamoDB.
    """
    print(f"Received {len(event['Records'])} messages")

    for record in event['Records']:
        try:
            # Read the message from SQS
            body = json.loads(record['body'])
            print(f"Processing: {body}")

            # Pull out the key fields
            device_id   = body.get('fogNodeId', 'unknown')
            timestamp   = body.get('timestamp', 
                         datetime.now(timezone.utc).isoformat())
            sensor_type = body.get('sensorType', 'unknown')
            raw_data    = body.get('rawData', {})
            theft       = body.get('theftDetected', False)
            alert_level = body.get('alertLevel', 'NORMAL')

            # Save to DynamoDB
            table.put_item(Item={
                'deviceId':      device_id,
                'timestamp':     timestamp,
                'sensorType':    sensor_type,
                'rawData':       json.dumps(raw_data),
                'theftDetected': theft,
                'alertLevel':    alert_level
            })

            print(f"✅ Saved to DynamoDB: {sensor_type} - {alert_level}")

        except Exception as e:
            print(f"❌ Error processing record: {e}")
            raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed successfully!')
    }