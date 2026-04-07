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
CLIENT_ID = "bike-guard-tilt"
TOPIC     = "bike/sensors/tilt"
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH  = os.getenv("KEY_PATH")
CA_PATH   = os.getenv("CA_PATH")

PUBLISH_INTERVAL = int(os.getenv("TILT_INTERVAL", "5"))

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

print("Tilt sensor connecting to AWS IoT Core...")
connection.connect().result()
print("Tilt sensor connected! ✅")

def generate_tilt():
    """
    Simulates a tilt sensor on a bike.
    Normal (leaning on stand): 15-20 degrees
    Theft (being lifted/carried): 45-90 degrees
    """
    if random.random() < 0.2:
        angle = round(random.uniform(45.0, 90.0), 1)
        status = "ALERT"
    else:
        angle = round(random.uniform(15.0, 20.0), 1)
        status = "NORMAL"

    return {
        "deviceId":   CLIENT_ID,
        "sensorType": "tilt",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "angle_deg":  angle,
        "status":     status
    }

if __name__ == "__main__":
    print(f"Sending tilt data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            payload = generate_tilt()
            publish_future, packet_id = connection.publish(
                topic=TOPIC,
                payload=json.dumps(payload),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result()
            print(f"📤 Sent: {payload}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping tilt sensor...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")