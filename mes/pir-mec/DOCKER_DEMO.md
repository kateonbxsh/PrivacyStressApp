# Guide de Démonstration (Version Docker)

Ce guide vous permet de relancer la démonstration complète du projet après votre redémarrage. Docker sera alors opérationnel.

## 1. Préparation (Une seule fois après le reboot)

Assurez-vous que le service Docker est bien démarré :
```bash
sudo systemctl start docker
```

## 2. Lancement de la démonstration

Ouvrez **3 terminaux** différents :

### TERMINAL 1 : L'Infrastructure MEC (Le Cœur)
C'est ici que vous verrez les logs de l'API, du broker MQTT et surtout de l'**agrégation FL**.
```bash
cd pir-mec
docker-compose up --build
```

### TERMINAL 2 : Le Smartphone (Simulation Utilisateur)
Ce script simule un utilisateur mobile qui envoie son stress et ses poids de modèle local.
```bash
cd pir-mec
./venv/bin/python scripts/simulate_phone.py
```
*(Note : Vous pouvez ouvrir un **Terminal 2bis** et relancer la même commande pour simuler un deuxième utilisateur et voir l'agrégation FedAvg se déclencher plus vite).*

### TERMINAL 3 : Le Contrôleur (Scénarios de Démo)
Ce script permet de modifier l'environnement "en direct" (bruit, foule, retard) pour montrer l'intelligence du MEC.
```bash
cd pir-mec
./venv/bin/python scripts/demo_control.py
```

---

## Ce qu'il faut montrer (Points clés)

1.  **Adaptation au Contexte** : Dans le **Terminal 2**, montrez que les recommandations changent dès que le **Terminal 3** modifie le contexte (ex: passage en mode "Incident").
2.  **Confidentialité FL** : Dans les logs du **Terminal 1**, montrez que le service `mec-fl` reçoit des vecteurs de nombres (poids) et non des données cardiaques brutes.
3.  **Intelligence Collective** : Montrez dans le **Terminal 1** le moment où le MEC calcule la moyenne FedAvg et publie le nouveau modèle global sur le réseau.
