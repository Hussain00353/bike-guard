import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('bike-guard-data')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def lambda_handler(event, context):
    try:
        # Scan with limit — much faster!
        response = table.scan(Limit=200)
        items_all = response.get('Items', [])

        # Sort newest first
        items_all.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        # Get latest 10 of each sensor type
        seen = {}
        items = []
        for item in items_all:
            sensor_type = item.get('sensorType', 'unknown')
            if sensor_type not in seen:
                seen[sensor_type] = 0
            if seen[sensor_type] < 10:
                items.append(item)
                seen[sensor_type] += 1

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'items': items,
                'count': len(items)
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }