import paho.mqtt.client as mqtt
import json
import time
import random

# Configuration
BROKER = "localhost"
PORT = 1883
TOPIC_PREDICTION = "tsa/prediction"
TOPIC_FL_UPDATE = "tsa/fl/update"
TOPIC_GLOBAL_MODEL = "tsa/fl/global_model"
CLIENT_ID = f"user_{random.randint(100, 999)}"
TOPIC_RECO = f"tsa/recommendation/{CLIENT_ID}"

def on_message(client, userdata, msg, properties=None):
    """Reçoit les messages du MEC (recommandations ou modèle global)."""
    payload = json.loads(msg.payload.decode())
    if msg.topic == TOPIC_GLOBAL_MODEL:
        print(f"\n[TÉLÉPHONE] Nouveau modèle global reçu ! Version: {payload.get('model_version')}")
    else:
        print(f"\n[TÉLÉPHONE] Recommandation reçue : {payload.get('recommendation')}")

# Configuration du client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, CLIENT_ID)
client.on_message = on_message

print(f"Connexion au broker {BROKER} en tant que {CLIENT_ID}...")
try:
    client.connect(BROKER, PORT)
except Exception as e:
    print(f"Erreur : Assurez-vous que docker-compose est lancé. ({e})")
    exit(1)

client.subscribe(TOPIC_RECO)
client.subscribe(TOPIC_GLOBAL_MODEL)
client.loop_start()

try:
    print("Simulation démarrée (Envoi stress + FL). Ctrl+C pour arrêter.")
    count = 0
    while True:
        count += 1
        
        # 1. Envoi du score de stress (Recommandation contextuelle)
        stress_score = round(random.uniform(0.1, 0.9), 2)
        payload_stress = {
            "client_id": CLIENT_ID,
            "risk_score": stress_score,
            "timestamp": time.time()
        }
        print(f"[TÉLÉPHONE] Envoi stress : {stress_score}")
        client.publish(TOPIC_PREDICTION, json.dumps(payload_stress))
        
        # 2. Envoi d'une mise à jour FL (Apprentissage fédéré)
        # On simule l'envoi de poids toutes les 2 itérations
        if count % 2 == 0:
            # On génère 4 poids aléatoires pour la démo
            fake_weights = [round(random.uniform(-1, 1), 4) for _ in range(4)]
            payload_fl = {
                "client_id": CLIENT_ID,
                "weights": fake_weights,
                "n_samples": random.randint(50, 200),
                "timestamp": time.time()
            }
            print(f"[TÉLÉPHONE] Envoi mise à jour FL (poids: {fake_weights[:2]}...)")
            client.publish(TOPIC_FL_UPDATE, json.dumps(payload_fl))
        
        time.sleep(5)

except KeyboardInterrupt:
    print("\nSimulation arrêtée.")
    client.loop_stop()
    client.disconnect()
