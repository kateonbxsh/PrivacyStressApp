import requests
import time
import json
import paho.mqtt.client as mqtt

API_URL = "http://localhost:8000/context/update"

def set_context(noise, crowd, delay, label):
    print(f"\n[DEMO] Passage au scénario : {label}")
    payload = {"noise": noise, "crowd": crowd, "delay": delay}
    try:
        requests.post(API_URL, json=payload)
        print(f"       -> Contexte mis à jour : Bruit={noise}, Foule={crowd}, Retard={delay}min")
    except:
        print("       -> Erreur : L'API MEC n'est pas accessible. Lancez docker-compose d'abord.")

if __name__ == "__main__":
    print("=== SYSTÈME DE CONTRÔLE DE LA DÉMO ===")
    
    # Scénario 1 : Tout va bien
    set_context(0.2, 0.3, 0, "Situation Normale")
    print("Regardez les recommandations sur le téléphone... (Attente 15s)")
    time.sleep(15)

    # Scénario 2 : Incident technique / Foule
    set_context(0.5, 0.9, 10, "Incident - Quai Bondé")
    print("Le MEC devrait maintenant conseiller d'éviter le quai... (Attente 15s)")
    time.sleep(15)

    # Scénario 3 : Environnement bruyant
    set_context(0.8, 0.4, 2, "Travaux - Bruit Excessif")
    print("Le MEC devrait conseiller un casque ou une zone calme... (Attente 15s)")
    
    print("\n[DEMO] Fin du cycle de démonstration contextuelle.")
