import time
import json
import random
from datetime import datetime, timezone
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
import os

load_dotenv()

ENDPOINT  = os.getenv("AWS_ENDPOINT")
CLIENT_ID = "bike-guard-gps"
TOPIC     = "bike/sensors/gps"
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH  = os.getenv("KEY_PATH")
CA_PATH   = os.getenv("CA_PATH")

# GPS updates less frequently - configurable!
PUBLISH_INTERVAL = int(os.getenv("GPS_INTERVAL", "10"))

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

print("GPS sensor connecting to AWS IoT Core...")
connection.connect().result()
print("GPS sensor connected! ✅")

# Dublin city centre as starting point
BASE_LAT = 53.3498
BASE_LON = -6.2603

def generate_gps():
    """
    Simulates a GPS sensor on a bike.
    Normally parked (tiny movement).
    During theft: bigger movement away from base.
    """
    # 20% chance of simulating movement (theft)
    if random.random() < 0.2:
        lat = round(BASE_LAT + random.uniform(0.001, 0.01), 6)
        lon = round(BASE_LON + random.uniform(0.001, 0.01), 6)
        status = "MOVING"
    else:
        lat = round(BASE_LAT + random.uniform(-0.0001, 0.0001), 6)
        lon = round(BASE_LON + random.uniform(-0.0001, 0.0001), 6)
        status = "PARKED"

    return {
        "deviceId":   CLIENT_ID,
        "sensorType": "gps",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "latitude":   lat,
        "longitude":  lon,
        "status":     status
    }

if __name__ == "__main__":
    print(f"Sending GPS data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            payload = generate_gps()
            publish_future, packet_id = connection.publish(
                topic=TOPIC,
                payload=json.dumps(payload),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result()
            print(f"📤 Sent: {payload}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping GPS sensor...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")