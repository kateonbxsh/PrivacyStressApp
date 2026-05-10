# Projet PIR - Détection du Stress (MEC & Federated Learning)

Ce projet implémente une architecture de détection du stress et de recommandation contextuelle utilisant le **Mobile Edge Computing (MEC)** et l'**Apprentissage Fédéré (Federated Learning)**.

## Architecture
Le système est divisé en trois composants principaux :
1. **L'Infrastructure MEC** : Gère l'agrégation des modèles et la logique de décision.
2. **Le Client (Smartphone)** : Simule un utilisateur envoyant des données de stress et des mises à jour de modèle.
3. **Le Contrôleur d'Environnement** : Simule les capteurs de la ville/gare (foule, bruit, retards).

---

## Guide de Lancement

Pour faire fonctionner la démonstration complète, vous devez ouvrir **3 terminaux** distincts dans le dossier `pir-mec`.

### 1. Terminal 1 : L'Infrastructure (Le Cerveau)
Ce terminal lance le broker MQTT, l'API de contexte et le service d'agrégation FL via Docker.
```bash
cd pir-mec
sudo docker-compose up --build
```
*Note : C'est ici que vous verrez passer les données de tous les utilisateurs et les moments où le modèle global est mis à jour.*

### 2. Terminal 2 : Le Smartphone (L'Utilisateur)
Ce script simule un voyageur qui envoie son niveau de stress et reçoit des recommandations personnalisées.
```bash
cd pir-mec
./venv/bin/python scripts/simulate_phone.py
```
*Note : Vous pouvez lancer ce script dans plusieurs terminaux pour simuler plusieurs utilisateurs simultanément.*

### 3. Terminal 3 : Le Contrôleur (L'Environnement)
Ce script permet de modifier le contexte de la gare en direct (ex: simuler un incident ou une foule dense).
```bash
cd pir-mec
./venv/bin/python scripts/demo_control.py
```
*Note : Observez comment les recommandations dans le Terminal 2 changent instantanément dès que vous modifiez le contexte ici.*

---

## Points clés de la démonstration
- **Confidentialité** : Les données cardiaques brutes ne quittent jamais le "téléphone", seuls les poids du modèle (FL) sont envoyés.
- **Réactivité** : Le MEC adapte ses conseils en temps réel selon les capteurs environnementaux.
- **Intelligence Collective** : Le modèle global s'améliore au fur et à mesure que les utilisateurs partagent leurs apprentissages locaux.
