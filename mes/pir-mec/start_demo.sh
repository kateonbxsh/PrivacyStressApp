#!/bin/bash

# Chemin vers le dossier racine du projet
PROJECT_ROOT="/mnt/data/insa_cours/PrivacyStressApp/mes/pir-mec"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

echo "=== DÉMARRAGE DES SERVICES MEC ==="

# 1. Lancer l'API
cd "$PROJECT_ROOT/api"
$VENV_PYTHON -m uvicorn app:app --host 0.0.0.0 --port 8000 > /tmp/mec_api.log 2>&1 &
API_PID=$!
echo "[OK] API lancée (PID: $API_PID)"

# 2. Lancer le service FL
cd "$PROJECT_ROOT/fl"
$VENV_PYTHON fl_service.py > /tmp/mec_fl.log 2>&1 &
FL_PID=$!
echo "[OK] Service FL lancé (PID: $FL_PID)"

# 3. Lancer le service de contexte
cd "$PROJECT_ROOT/context"
$VENV_PYTHON context_service.py > /tmp/mec_context.log 2>&1 &
CONTEXT_PID=$!
echo "[OK] Service Contexte lancé (PID: $CONTEXT_PID)"

echo "------------------------------------------------"
echo "Les services tournent en arrière-plan."
echo "Pour voir les logs du FL : tail -f /tmp/mec_fl.log"
echo "------------------------------------------------"

# Fonction pour arrêter proprement les services à la fin
cleanup() {
    echo -e "\nArrêt des services..."
    kill $API_PID $FL_PID $CONTEXT_PID
    exit
}

trap cleanup SIGINT

# 4. Lancer la simulation du téléphone (bloquant pour garder le script actif)
echo "Lancement de la simulation utilisateur..."
cd "$PROJECT_ROOT/scripts"
$VENV_PYTHON simulate_phone.py
