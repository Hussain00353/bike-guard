import json
import time
from datetime import datetime, timezone
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
import os

# ─────────────────────────────────────────────
# Load settings from .env file
# ─────────────────────────────────────────────
load_dotenv()

ENDPOINT  = os.getenv("AWS_ENDPOINT")
CLIENT_ID = "bike-guard-fog-node"
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH  = os.getenv("KEY_PATH")
CA_PATH   = os.getenv("CA_PATH")

# Topics to listen to (all 5 sensors)
SENSOR_TOPICS = [
    "bike/sensors/vibration",
    "bike/sensors/gps",
    "bike/sensors/tilt",
    "bike/sensors/sound",
    "bike/sensors/battery",
]

# Topic to send processed data to the cloud backend
DISPATCH_TOPIC = "bike/fog/processed"

# ─────────────────────────────────────────────
# Fog node memory - tracks recent sensor states
# ─────────────────────────────────────────────
sensor_states = {
    "vibration": "NORMAL",
    "gps":       "PARKED",
    "tilt":      "NORMAL",
    "sound":     "NORMAL",
    "battery":   "GOOD",
}

def check_theft_alert():
    """
    The fog node's brain.
    Looks at all sensor states and decides if theft is happening.
    If 2 or more sensors are in alert state = THEFT DETECTED!
    This is the fog processing logic - runs locally, no cloud needed.
    """
    alert_count = 0

    if sensor_states["vibration"] == "ALERT":
        alert_count += 1
    if sensor_states["gps"] == "MOVING":
        alert_count += 1
    if sensor_states["tilt"] == "ALERT":
        alert_count += 1
    if sensor_states["sound"] == "ALARM":
        alert_count += 1

    # 2 or more sensors alerting = theft
    return alert_count >= 2

def on_message_received(topic, payload, **kwargs):
    """
    This function runs every time a sensor sends a message.
    It reads the message, updates the sensor state,
    then decides what to dispatch to the cloud.
    """
    try:
        # Read the incoming sensor message
        data = json.loads(payload.decode())
        sensor_type = data.get("sensorType", "unknown")
        status      = data.get("status", "NORMAL")

        print(f"\n📥 Fog received [{topic}]: {data}")

        # Update our memory of this sensor's state
        if sensor_type in sensor_states:
            sensor_states[sensor_type] = status

        # ── Fog processing logic ──────────────────
        theft_detected = check_theft_alert()

        # Build the processed payload to send to cloud
        processed = {
            "fogNodeId":      CLIENT_ID,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "sensorType":     sensor_type,
            "rawData":        data,
            "sensorStates":   dict(sensor_states),
            "theftDetected":  theft_detected,
            "alertLevel":     "CRITICAL" if theft_detected else "NORMAL"
        }

        # Dispatch to cloud backend topic
        connection.publish(
            topic=DISPATCH_TOPIC,
            payload=json.dumps(processed),
            qos=mqtt.QoS.AT_LEAST_ONCE
        )

        if theft_detected:
            print(f"🚨 THEFT DETECTED! Dispatched alert to cloud!")
        else:
            print(f"✅ Normal reading. Dispatched to cloud.")

    except Exception as e:
        print(f"❌ Error processing message: {e}")

# ─────────────────────────────────────────────
# Connect to AWS IoT Core
# ─────────────────────────────────────────────
io.init_logging(getattr(io.LogLevel, 'Fatal'), 'stderr')

connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=KEY_PATH,
    ca_filepath=CA_PATH,
    client_id=CLIENT_ID,
    clean_session=True,
    keep_alive_secs=60
)

print("🧠 Fog node connecting to AWS IoT Core...")
connection.connect().result()
print("🧠 Fog node connected! ✅\n")

# Subscribe to all 5 sensor topics
for topic in SENSOR_TOPICS:
    subscribe_future, packet_id = connection.subscribe(
        topic=topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )
    subscribe_future.result()
    print(f"📡 Subscribed to: {topic}")

print("\n🧠 Fog node is running and listening for sensor data...")
print("Press Ctrl+C to stop\n")

# ─────────────────────────────────────────────
# Keep running forever until Ctrl+C
# ─────────────────────────────────────────────
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping fog node...")
finally:
    connection.disconnect().result()
    print("Fog node disconnected.")