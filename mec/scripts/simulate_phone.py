import json
import random
import time

import paho.mqtt.client as mqtt
import requests

BROKER = "localhost"
PORT = 1883
MEC_API_URL = "http://localhost:8000"
TOPIC_PREDICTION = "tsa/prediction"
TOPIC_FL_UPDATE = "tsa/fl/update"
TOPIC_GLOBAL_MODEL = "tsa/fl/global_model"
CLIENT_ID = f"user_{random.randint(100, 999)}"
TOPIC_RECO = f"tsa/recommendation/{CLIENT_ID}"

LEARNING_RATE_SHARED = 0.04
LEARNING_RATE_PERSONAL = 0.08

personal_weights = None
shared_weights = None


def sigmoid(value):
    return 1.0 / (1.0 + pow(2.718281828, -value))


def initialize_from_mec():
    global personal_weights, shared_weights
    try:
        response = requests.get(f"{MEC_API_URL}/fl/model", timeout=5)
        response.raise_for_status()
        model = response.json()
        shared_weights = [float(value) for value in model["sharedWeights"]]
        personal_weights = [0.0 for _ in shared_weights]
        print(f"[PHONE] Initialized ws from MEC {model.get('version')} and vi=0")
    except Exception as exc:
        shared_weights = [0.18, 0.22, 0.2, 0.16, 0.12, 0.14, 0.1, 0.12, -0.55]
        personal_weights = [0.0 for _ in shared_weights]
        print(f"[PHONE] MEC init failed, using local default ws and vi=0: {exc}")


def on_message(client, userdata, msg, properties=None):
    global shared_weights
    payload = json.loads(msg.payload.decode())
    if msg.topic == TOPIC_GLOBAL_MODEL:
        incoming = payload.get("sharedWeights")
        if isinstance(incoming, list):
            shared_weights = [float(value) for value in incoming]
            print(f"\n[PHONE] Regional ws replaced from MEC model {payload.get('model_version')}; vi preserved")
    else:
        print(f"\n[PHONE] Recommendation received: {payload.get('recommendation')}")


def local_train_step(features, target):
    """Update ws and vi locally, but return only ws for federation."""
    effective = [s + p for s, p in zip(shared_weights, personal_weights)]
    prediction = sigmoid(sum(weight * value for weight, value in zip(effective, features)))
    gradient_scale = prediction - target

    for index, feature in enumerate(features):
        gradient = gradient_scale * feature
        shared_weights[index] -= LEARNING_RATE_SHARED * gradient
        personal_weights[index] -= LEARNING_RATE_PERSONAL * gradient

    return prediction


initialize_from_mec()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
client.on_message = on_message

print(f"Connecting to broker {BROKER} as {CLIENT_ID}...")
try:
    client.connect(BROKER, PORT)
except Exception as exc:
    print(f"Error: start docker compose first. ({exc})")
    raise SystemExit(1)

client.subscribe(TOPIC_RECO)
client.subscribe(TOPIC_GLOBAL_MODEL)
client.loop_start()

try:
    print("Personalized FL phone simulation started. Press Ctrl+C to stop.")
    count = 0
    while True:
        count += 1
        stress_score = round(random.uniform(0.1, 0.9), 2)
        features = [
            stress_score,
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            random.uniform(0.0, 1.0),
            1.0,
        ]
        target = 1.0 if stress_score >= 0.55 else 0.0
        prediction = local_train_step(features, target)

        client.publish(
            TOPIC_PREDICTION,
            json.dumps({"client_id": CLIENT_ID, "risk_score": stress_score, "timestamp": time.time()}),
        )

        if count % 2 == 0:
            payload_fl = {
                "client_id": CLIENT_ID,
                "shared_weights": [round(value, 8) for value in shared_weights],
                "n_samples": random.randint(50, 200),
                "timestamp": time.time(),
                "personal_component_included": False,
            }
            print(f"[PHONE] Sent shared ws update only; vi norm={sum(abs(v) for v in personal_weights):.4f}")
            client.publish(TOPIC_FL_UPDATE, json.dumps(payload_fl))

        print(f"[PHONE] Local effective wi inference={prediction:.3f}; stress={stress_score}")
        time.sleep(5)

except KeyboardInterrupt:
    print("\nSimulation stopped.")
    client.loop_stop()
    client.disconnect()
