import json
import os
import time

import paho.mqtt.client as mqtt
import requests

from aggregator import fedavg

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:4000/api").rstrip("/")
MEC_API_URL = os.getenv("MEC_API_URL", "http://localhost:8000").rstrip("/")
MEC_NODE_NAME = os.getenv("MEC_NODE_NAME", "MEC Local")
MEC_REGION = os.getenv("MEC_REGION", "local-demo")

TOPIC_UPDATE = "tsa/fl/update"
TOPIC_GLOBAL_MODEL = "tsa/fl/global_model"

MIN_UPDATES_FOR_AGGREGATION = int(os.getenv("MIN_UPDATES_FOR_AGGREGATION", "3"))
updates_buffer = []


def update_norm(weights):
    return float(sum(abs(float(weight)) for weight in weights))


def notify_cloud(round_id, aggregated_from, weights):
    """Forward only regional aggregate metadata to the cloud backend."""
    payload = {
        "clientId": f"{MEC_NODE_NAME}-regional-aggregator",
        "mecNodeName": MEC_NODE_NAME,
        "region": MEC_REGION,
        "round": round_id,
        "sampleCount": aggregated_from,
        "updateNorm": update_norm(weights),
        "sharedWeights": weights,
        "metrics": {
            "aggregation": "regional_fedavg",
            "aggregatedFrom": aggregated_from,
            "hierarchy": "device_to_mec_to_cloud",
        },
    }

    try:
        response = requests.post(
            f"{BACKEND_API_URL}/federated/updates",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        print(f"[FL] Cloud sync accepted: {body.get('aggregation', {})}")
    except Exception as exc:
        print(f"[FL] Cloud sync skipped/failed: {exc}")


def update_local_mec_model(round_id, aggregated_from, weights):
    try:
        response = requests.post(
            f"{MEC_API_URL}/fl/model",
            json={
                "version": f"mec-r{round_id}",
                "sharedWeights": weights,
                "sampleCount": aggregated_from,
            },
            timeout=5,
        )
        response.raise_for_status()
        print("[FL] Local MEC shared model updated")
    except Exception as exc:
        print(f"[FL] Local MEC model update skipped/failed: {exc}")


def on_message(client, userdata, msg, properties=None):
    global updates_buffer

    try:
        payload = json.loads(msg.payload.decode())
        client_id = payload.get("client_id", "unknown")
        print(f"[FL] Received update from {client_id} ({payload.get('n_samples')} samples)")

        updates_buffer.append(payload)

        if len(updates_buffer) >= MIN_UPDATES_FOR_AGGREGATION:
            print(f"[FL] Aggregating {len(updates_buffer)} device updates with FedAvg")
            new_weights = fedavg(updates_buffer)

            if new_weights:
                round_id = int(time.time())
                regional_model = {
                    "model_version": f"mec-r{round_id}",
                    "sharedWeights": new_weights,
                    "aggregated_from": len(updates_buffer),
                    "mec_node": MEC_NODE_NAME,
                    "region": MEC_REGION,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                update_local_mec_model(round_id, len(updates_buffer), new_weights)
                notify_cloud(round_id, len(updates_buffer), new_weights)
                client.publish(TOPIC_GLOBAL_MODEL, json.dumps(regional_model))
                print(f"[FL] Regional model published on {TOPIC_GLOBAL_MODEL}")
                updates_buffer = []
            else:
                print("[FL] Aggregation failed.")

    except Exception as exc:
        print(f"[FL] Error: {exc}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

try:
    print(f"[FL] Connecting to MQTT broker ({MQTT_BROKER}:{MQTT_PORT})")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(TOPIC_UPDATE)
    print(f"[FL] Waiting for device updates on {TOPIC_UPDATE}")
    client.loop_forever()
except Exception as exc:
    print(f"[FL] Could not start FL service: {exc}")
