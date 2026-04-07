import json
import boto3
from decimal import Decimal
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────
# Flask app setup
# Elastic Beanstalk looks for 'application' variable
# ─────────────────────────────────────────────
application = Flask(__name__, static_folder='dashboard')
CORS(application)

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('bike-guard-data')

class DecimalEncoder(json.JSONEncoder):
    """Converts DynamoDB Decimal types to float for JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@application.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('dashboard', 'index.html')

@application.route('/style.css')
def css():
    """Serve the CSS file"""
    return send_from_directory('dashboard', 'style.css')

@application.route('/app.js')
def js():
    """Serve the JavaScript file"""
    return send_from_directory('dashboard', 'app.js')

@application.route('/data')
def get_data():
    try:
        # Only get last 30 minutes of data
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()

        response = table.scan(
            FilterExpression='#ts > :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':cutoff': cutoff}
        )
        items_all = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#ts > :cutoff',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={':cutoff': cutoff},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items_all.extend(response.get('Items', []))

        items_all.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        seen = {}
        items = []
        for item in items_all:
            sensor_type = item.get('sensorType', 'unknown')
            if sensor_type not in seen:
                seen[sensor_type] = 0
            if seen[sensor_type] < 10:
                items.append(item)
                seen[sensor_type] += 1

        return application.response_class(
            response=json.dumps({
                'items': items,
                'count': len(items)
            }, cls=DecimalEncoder),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# ─────────────────────────────────────────────
# Run the app
# ─────────────────────────────────────────────
if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=False)