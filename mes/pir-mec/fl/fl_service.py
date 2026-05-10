import os
import json
import time
import paho.mqtt.client as mqtt
from aggregator import fedavg

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
TOPIC_UPDATE = "tsa/fl/update"
TOPIC_GLOBAL_MODEL = "tsa/fl/global_model"

# Paramètres de l'agrégation
MIN_UPDATES_FOR_AGGREGATION = 3  # On agrège dès qu'on a 3 mises à jour
updates_buffer = []

def on_message(client, userdata, msg):
    global updates_buffer
    
    try:
        payload = json.loads(msg.payload.decode())
        client_id = payload.get("client_id", "unknown")
        print(f"[FL] Reçu mise à jour de {client_id} ({payload.get('n_samples')} échantillons)")
        
        updates_buffer.append(payload)
        
        if len(updates_buffer) >= MIN_UPDATES_FOR_AGGREGATION:
            print(f"[FL] Seuil atteint ({MIN_UPDATES_FOR_AGGREGATION}). Lancement de l'agrégation...")
            
            new_weights = fedavg(updates_buffer)
            
            if new_weights:
                # Préparation du modèle global
                global_model = {
                    "model_version": f"v{int(time.time())}",
                    "weights": new_weights,
                    "aggregated_from": len(updates_buffer),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                
                # Publication du modèle agrégé
                client.publish(TOPIC_GLOBAL_MODEL, json.dumps(global_model))
                print(f"[FL] Modèle global publié sur {TOPIC_GLOBAL_MODEL}")
                
                # Vidage du buffer après succès
                updates_buffer = []
            else:
                print("[FL] Erreur lors de l'agrégation.")
                
    except Exception as e:
        print(f"[FL] Erreur : {e}")

# Setup MQTT
client = mqtt.Client()
client.on_message = on_message

try:
    print(f"[FL] Connexion au broker MQTT ({MQTT_BROKER}:{MQTT_PORT})...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(TOPIC_UPDATE)
    print(f"[FL] En attente de mises à jour sur {TOPIC_UPDATE}...")
    client.loop_forever()
except Exception as e:
    print(f"[FL] Impossible de démarrer le service FL : {e}")
