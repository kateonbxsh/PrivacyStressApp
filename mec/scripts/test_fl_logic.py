import sys
import os
sys.path.append(os.path.join(os.getcwd(), "fl"))

from aggregator import fedavg

def test_fedavg():
    # Test 1 : Moyenne simple de deux modèles identiques
    updates = [
        {"weights": [1.0, 2.0], "n_samples": 100},
        {"weights": [1.0, 2.0], "n_samples": 100}
    ]
    result = fedavg(updates)
    assert result == [1.0, 2.0], f"Erreur Test 1: {result}"
    
    # Test 2 : Moyenne pondérée (le 2ème modèle a 3x plus d'importance)
    updates = [
        {"weights": [0.0, 0.0], "n_samples": 10},
        {"weights": [4.0, 8.0], "n_samples": 30}
    ]
    # (10*0 + 30*4) / 40 = 120/40 = 3.0
    # (10*0 + 30*8) / 40 = 240/40 = 6.0
    result = fedavg(updates)
    assert result == [3.0, 6.0], f"Erreur Test 2: {result}"

    print("✅ Tous les tests FedAvg sont passés avec succès !")

if __name__ == "__main__":
    try:
        test_fedavg()
    except Exception as e:
        print(f"❌ Échec des tests : {e}")
