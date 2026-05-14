import sys
import os

# Ajout du dossier context au chemin d'import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'context'))

# Mocking (simulacre) de l'API et du Client MQTT
# Pourquoi ? Parce qu'on veut tester la LOGIQUE sans avoir besoin de réseau.
import context_service

class MockClient:
    def publish(self, topic, payload):
        print(f"   [PUBLICATION MQTT] Topic: {topic}")
        print(f"   [CONTENU MESSAGE] {payload}")

class MockMsg:
    def __init__(self, payload):
        self.payload = payload.encode()

# On remplace la fonction qui interroge l'API par une fausse fonction
# Pourquoi ? Parce que l'API n'est pas lancée.
def mock_get_context(crowd=0.0):
    return {"zone": "Station_Test", "crowd": crowd, "noise": 0.1, "delay": 0}

# --- SCÉNARIO 1 : Stress élevé et foule dense ---
print("\n--- TEST 1 : Stress Élevé + Foule ---")
context_service.get_current_context = lambda: mock_get_context(crowd=0.9)
msg = MockMsg('{"client_id": "test_01", "risk_score": 0.85}')
context_service.on_message(MockClient(), None, msg)

# --- SCÉNARIO 2 : Stress faible ---
print("\n--- TEST 2 : Stress Faible ---")
context_service.get_current_context = lambda: mock_get_context(crowd=0.1)
msg = MockMsg('{"client_id": "test_01", "risk_score": 0.1}')
context_service.on_message(MockClient(), None, msg)
