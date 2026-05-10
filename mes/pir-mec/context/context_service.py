import os
import json
import time
import requests

try:
    import paho.mqtt.client as mqtt
except ImportError:
    # On définit un faux client MQTT pour les tests locaux sans bibliothèque
    class mqtt:
        class Client:
            def __getattr__(self, name): return lambda *a, **k: None
    print("[INFO] paho-mqtt non trouvé. Mode test activé.")

# Configuration portable (Docker ou Local)
# Pourquoi on utilise os.getenv() ? 
# Parce que Docker nous donne l'adresse via l'environnement, 
# sinon on utilise "localhost" par défaut sur votre machine.
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
API_URL = os.getenv("API_URL", "http://localhost:8000/context")

def get_current_context():
    """Récupère le contexte local via l'API FastAPI."""
    try:
        # Dans Docker, l'URL sera http://api:8000/context
        response = requests.get(API_URL, timeout=2)
        return response.json()
    except Exception as e:
        print(f"Erreur lors de la récupération du contexte via l'API : {e}")
        return None

def on_message(client, userdata, msg):
    """
    Fonction appelée automatiquement par le client MQTT 
    chaque fois qu'un message arrive sur le topic 'tsa/prediction'.
    """
    try:
        # Décodage du message JSON reçu du téléphone
        payload = json.loads(msg.payload.decode())
        client_id = payload.get("client_id", "unknown")
        risk_score = payload.get("risk_score", 0.0)
        
        print(f"\n[REÇU] Stress de l'utilisateur '{client_id}': {risk_score}")
        
        # Récupération du contexte environnemental (bruit, foule...)
        context = get_current_context()
        if not context:
            print("[ERREUR] Impossible de prendre une décision sans contexte.")
            return

        # ---------------------------------------------------------------------
        # LOGIQUE DE DÉCISION : Stress + Contexte local
        # ---------------------------------------------------------------------
        noise = context.get('noise', 0)
        crowd = context.get('crowd', 0)
        delay = context.get('delay', 0)

        if risk_score > 0.7:
            if crowd > 0.7:
                recommendation_message = "Foule dense détectée. Dirigez-vous vers la zone de repos (Secteur B)."
            elif noise > 0.7:
                recommendation_message = "Bruit excessif. Nous vous conseillons de porter un casque ou de changer de quai."
            elif delay > 5:
                recommendation_message = f"Retard de {delay} min. Évitez l'attente sur le quai, préférez le hall principal."
            else:
                recommendation_message = "Stress élevé détecté. Prenez un moment pour respirer, le trajet est sous contrôle."
        elif risk_score > 0.4:
            if crowd > 0.5 or noise > 0.5:
                recommendation_message = "Ambiance chargée. Une zone calme est disponible à 50m."
            else:
                recommendation_message = "Légère tension. Tout semble calme autour de vous."
        else:
            recommendation_message = "Situation normale. Bonne route !"
        # ---------------------------------------------------------------------
        # FIN DE VOTRE LOGIQUE
        # ---------------------------------------------------------------------

        # Préparation de la réponse
        response_topic = f"tsa/recommendation/{client_id}"
        response_payload = {
            "client_id": client_id,
            "recommendation": recommendation_message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Envoi de la recommandation via MQTT
        client.publish(response_topic, json.dumps(response_payload))
        print(f"[ENVOI] Recommandation pour {client_id} : {recommendation_message}")

    except Exception as e:
        print(f"Erreur critique dans le service de recommandation : {e}")

# Initialisation du client MQTT
client = mqtt.Client()
client.on_message = on_message

try:
    print(f"Connexion au broker MQTT ({MQTT_BROKER}:{MQTT_PORT})...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # On s'abonne au flux de prédictions venant des téléphones
    client.subscribe("tsa/prediction")
    
    print("Service de recommandation prêt et en attente de messages.")
    client.loop_forever()
except Exception as e:
    print(f"Impossible de démarrer le service : {e}")
