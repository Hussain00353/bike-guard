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
CLIENT_ID = "bike-guard-sound"
TOPIC     = "bike/sensors/sound"
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH  = os.getenv("KEY_PATH")
CA_PATH   = os.getenv("CA_PATH")

PUBLISH_INTERVAL = int(os.getenv("SOUND_INTERVAL", "5"))

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

print("Sound sensor connecting to AWS IoT Core...")
connection.connect().result()
print("Sound sensor connected! ✅")

def generate_sound():
    """
    Simulates a sound/alarm sensor on a bike.
    Normal ambient noise: 30-50 dB
    Alarm triggered:      80-120 dB
    """
    if random.random() < 0.2:
        db = round(random.uniform(80.0, 120.0), 1)
        status = "ALARM"
    else:
        db = round(random.uniform(30.0, 50.0), 1)
        status = "NORMAL"

    return {
        "deviceId":   CLIENT_ID,
        "sensorType": "sound",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "decibels":   db,
        "status":     status
    }

if __name__ == "__main__":
    print(f"Sending sound data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            payload = generate_sound()
            publish_future, packet_id = connection.publish(
                topic=TOPIC,
                payload=json.dumps(payload),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result()
            print(f"📤 Sent: {payload}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping sound sensor...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")