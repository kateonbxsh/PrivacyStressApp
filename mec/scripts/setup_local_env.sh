#!/bin/bash
# Script pour initialiser l'environnement de développement local (hors Docker)

echo "--- Création de l'environnement virtuel Python ---"
python -m venv venv

echo "--- Activation et installation des dépendances ---"
# Note: On utilise 'python -m pip' pour être sûr de pointer sur le bon environnement
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r api/requirements.txt

echo "--- Terminé ---"
echo "Pour activer l'environnement, lancez : source venv/bin/activate"
