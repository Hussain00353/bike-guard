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
CLIENT_ID = "bike-guard-battery"
TOPIC     = "bike/sensors/battery"
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH  = os.getenv("KEY_PATH")
CA_PATH   = os.getenv("CA_PATH")

# Battery checks less often - configurable!
PUBLISH_INTERVAL = int(os.getenv("BATTERY_INTERVAL", "30"))

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

print("Battery sensor connecting to AWS IoT Core...")
connection.connect().result()
print("Battery sensor connected! ✅")

# Battery slowly drains over time
battery_level = 100.0

def generate_battery():
    """
    Simulates battery level slowly draining.
    LOW battery = system vulnerability!
    """
    global battery_level
    # Drain between 0.1 and 0.5% each reading
    battery_level = max(0.0, battery_level - round(random.uniform(0.1, 0.5), 1))

    if battery_level < 20.0:
        status = "LOW"
    elif battery_level < 50.0:
        status = "MEDIUM"
    else:
        status = "GOOD"

    return {
        "deviceId":        CLIENT_ID,
        "sensorType":      "battery",
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "battery_percent": round(battery_level, 1),
        "status":          status
    }

if __name__ == "__main__":
    print(f"Sending battery data every {PUBLISH_INTERVAL} seconds...")
    print("Press Ctrl+C to stop\n")
    try:
        while True:
            payload = generate_battery()
            publish_future, packet_id = connection.publish(
                topic=TOPIC,
                payload=json.dumps(payload),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result()
            print(f"📤 Sent: {payload}")
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping battery sensor...")
    finally:
        connection.disconnect().result()
        print("Disconnected.")