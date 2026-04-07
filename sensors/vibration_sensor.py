import time
import json
import random
from datetime import datetime, timezone
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
import os

# ─────────────────────────────────────
# Load settings from .env file
# ─────────────────────────────────────
load_dotenv()

ENDPOINT   = os.getenv("AWS_ENDPOINT")
CLIENT_ID  = "bike-guard-vibration"
TOPIC      = "bike/sensors/vibration"
CERT_PATH  = os.getenv("CERT_PATH")
KEY_PATH   = os.getenv("KEY_PATH")
CA_PATH    = os.getenv("CA_PATH")

# How often to send data (seconds) - configurable!
PUBLISH_INTERVAL = int(os.getenv("VIBRATION_INTERVAL", "5"))

# ─────────────────────────────────────
# Connect to AWS IoT Core (same as lab!)
# ─────────────────────────────────────
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

print("Vibration sensor connecting to AWS IoT Core...")
connection.connect().result()
print("Vibration sensor connected! ✅")

# ─────────────────────────────────────
# Generate fake vibration data
# ─────────────────────────────────────
def generate_vibration():
    """
    Simulates a vibration sensor on a bike.
    Normal vibration (parked): 0.0 - 1.5 G
    Theft attempt (shaking):   2.0 - 8.0 G
    """
    # 20% chance of simulating a theft attempt
    if random.random() < 0.2:
        vibration = round(random.uniform(2.0, 8.0), 2)
        status = "ALERT"
    else:
        vibration = round(random.uniform(0.0, 1.5), 2)
        status = "NORMAL"

    return {
        "deviceId":    CLIENT_ID,
        "sensorType":  "vibration",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "vibration_g": vibration,
        "status":      status
    }

# ─────────────────────────────────────
# Keep sending data forever
# ─────────────────────────────────────
if __name__ == "__main__":
    print(f"Sending vibration data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            payload = generate_vibration()
            publish_future, packet_id = connection.publish(
                topic=TOPIC,
                payload=json.dumps(payload),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result()
            print(f"📤 Sent: {payload}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping vibration sensor...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")