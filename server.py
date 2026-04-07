import json
import boto3
from decimal import Decimal
from http.server import HTTPServer, BaseHTTPRequestHandler

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('bike-guard-data')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        # ── API endpoint ──────────────────────
        if self.path.startswith('/data'):
            try:
                # Get ALL items (handle pagination)
                items_all = []
                response = table.scan()
                items_all.extend(response.get('Items', []))
                while 'LastEvaluatedKey' in response:
                    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                    items_all.extend(response.get('Items', []))
                
                # Sort by timestamp newest first
                items_all.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # Get latest 10 of EACH sensor type
                from collections import defaultdict
                by_type = defaultdict(list)
                for item in items_all:
                    sensor_type = item.get('sensorType', 'unknown')
                    if len(by_type[sensor_type]) < 10:
                        by_type[sensor_type].append(item)
                
                # Flatten back to list
                items = []
                for type_items in by_type.values():
                    items.extend(type_items)
                body = json.dumps({
                    'items': items,
                    'count': len(items)
                }, cls=DecimalEncoder).encode()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        # ── Serve dashboard files ─────────────
        else:
            path = self.path.lstrip('/')
            if path == '' or path == 'index.html':
                filepath = 'dashboard/index.html'
                ctype = 'text/html'
            elif path == 'style.css':
                filepath = 'dashboard/style.css'
                ctype = 'text/css'
            elif path == 'app.js':
                filepath = 'dashboard/app.js'
                ctype = 'application/javascript'
            else:
                self.send_response(404)
                self.end_headers()
                return

            try:
                with open(filepath, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(404)
                self.end_headers()

if __name__ == '__main__':
    print("🚲 BikeGuard server running on port 8082...")
    print("Open: https://6e8e3c0e3b1b4aad8ab458d59d502dd7.vfs.cloud9.us-east-1.amazonaws.com:8082")
    HTTPServer(('0.0.0.0', 8082), Handler).serve_forever()