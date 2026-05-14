# Plan détaillé de mise en place du MEC pour le projet PIR TSA / mobilité intelligente

## 1. Objectif de la partie MEC

Le nœud MEC (Multi-access Edge Computing) est le **serveur local** proche des téléphones. Dans ce projet, il a quatre rôles principaux :

1. **Recevoir des informations des téléphones** de manière sécurisée.
2. **Intégrer le contexte local** de mobilité (bruit, affluence, perturbation, retard, etc.).
3. **Servir de niveau intermédiaire pour l’apprentissage fédéré** en recevant les mises à jour des modèles locaux.
4. **Réagir rapidement** sans dépendre entièrement du backend central.

Dans la phase de prototype, le MEC sera **simulé sur un PC Arch Linux**.

---

## 2. Architecture cible du prototype MEC

```text
[ Téléphones / clients simulés ]
          |
          | MQTTs / HTTPS
          v
[ MEC sur PC ]
   ├── Docker Engine
   ├── Mosquitto (broker MQTT)
   ├── API FastAPI
   ├── Service contexte local
   ├── Service FL (agrégation locale)
   └── Logs / monitoring
          |
          | HTTPS
          v
[ Backend central ]
```

### Répartition des rôles

- **Téléphone**
  - garde les données brutes sensibles ;
  - exécute le modèle local ;
  - envoie une prédiction minimale ou une mise à jour FL.

- **MEC**
  - reçoit les messages ;
  - agrège les mises à jour FL ;
  - combine prédiction individuelle + contexte local ;
  - renvoie une recommandation locale.

- **Backend**
  - agrégation globale ;
  - gestion des versions de modèles ;
  - supervision longue durée.

---

## 3. Données qui transitent par le MEC

### 3.1 Données qui ne doivent idéalement **pas** quitter le téléphone

- rythme cardiaque brut ;
- localisation brute détaillée ;
- historique complet de déplacements ;
- données comportementales directement identifiantes.

### 3.2 Données qui peuvent être envoyées au MEC

- score de risque produit par le modèle local ;
- identifiant pseudonymisé ;
- zone ou station courante ;
- mise à jour FL (poids, gradients, delta de paramètres) ;
- métadonnées minimales d’entraînement (`n_samples`, version du modèle, timestamp).

### 3.3 Données qui peuvent être envoyées du MEC vers le backend

- mises à jour FL déjà agrégées localement ;
- métriques globales locales ;
- version de modèle ;
- statistiques techniques.

---

## 4. Choix technologiques recommandés

### 4.1 Base du MEC

- **OS** : Arch Linux
- **Conteneurisation** : Docker
- **Orchestration simple** : Docker Compose
- **Broker MQTT** : Eclipse Mosquitto
- **API MEC** : FastAPI
- **Client MQTT Python** : paho-mqtt
- **Calcul FL / logique métier** : Python + NumPy / PyTorch selon la suite du projet

### 4.2 Pourquoi ces choix

- Docker simplifie le déploiement et évite les conflits de dépendances.
- Mosquitto est léger, standard et adapté aux communications IoT / temps réel.
- FastAPI est simple pour exposer des routes de contrôle et de debug.
- Python permet de faire rapidement l’agrégation FL et la logique de décision.

---

## 5. Étape 1 — Préparer la machine MEC

### 5.1 Mise à jour système

```bash
sudo pacman -Syu
```

### 5.2 Installer les paquets utiles

```bash
sudo pacman -S docker docker-compose python python-pip python-virtualenv git curl jq
```

### 5.3 Installer le client MQTT local pour les tests (optionnel mais pratique)

```bash
sudo pacman -S mosquitto
```

Tu pourras ensuite tester avec :

```bash
mosquitto_pub --help
mosquitto_sub --help
```

---

## 6. Étape 2 — Installer et configurer Docker

### 6.1 Démarrer Docker

```bash
sudo systemctl start docker
```

### 6.2 Activer Docker au démarrage

```bash
sudo systemctl enable docker
sudo systemctl enable containerd
```

### 6.3 Vérifier le fonctionnement

```bash
sudo docker run hello-world
```

### 6.4 Éviter de taper `sudo` à chaque fois

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

Puis vérifier :

```bash
docker run hello-world
```

### 6.5 Attention sécurité

L’ajout au groupe `docker` donne des privilèges élevés sur la machine. Pour un projet étudiant sur machine locale, c’est généralement acceptable, mais il faut le mentionner dans le rapport.

---

## 7. Étape 3 — Créer l’arborescence du projet MEC

Créer un dossier de travail :

```bash
mkdir -p ./mec/{mosquitto/{config,data,log},api,fl,context,scripts}
cd ./mec
```

Arborescence cible :

```text
mec/
├── docker-compose.yml
├── .env
├── mosquitto/
│   ├── config/
│   │   └── mosquitto.conf
│   ├── data/
│   └── log/
├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── fl/
│   ├── aggregator.py
│   ├── model_store.py
│   └── requirements.txt
├── context/
│   ├── context_service.py
│   └── context.json
└── scripts/
    ├── test_pub.sh
    └── test_sub.sh
```

---

## 8. Étape 4 — Déployer Mosquitto dans Docker

### 8.1 Créer une configuration minimale

Fichier : `./mec/mosquitto/config/mosquitto.conf`

```conf
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

> Pour la première mise en place, on commence sans authentification pour simplifier les tests. Ensuite, on passera à TLS + mot de passe.

### 8.2 Lancer Mosquitto directement avec Docker (test rapide)

```bash
docker run -d \
  --name mec-mosquitto \
  -p 1883:1883 \
  -v "$PWD/mosquitto/config:/mosquitto/config" \
  -v "$PWD/mosquitto/data:/mosquitto/data" \
  -v "$PWD/mosquitto/log:/mosquitto/log" \
  eclipse-mosquitto:2
```

### 8.3 Vérifier les logs

```bash
docker logs -f mec-mosquitto
```

### 8.4 Tester localement le broker

Terminal 1 :

```bash
mosquitto_sub -h localhost -t 'tsa/test'
```

Terminal 2 :

```bash
mosquitto_pub -h localhost -t 'tsa/test' -m 'bonjour MEC'
```

Si le message apparaît, le broker fonctionne.

---

## 9. Étape 5 — Passer à Docker Compose

Créer `docker-compose.yml` :

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mec-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - ./mosquitto/config:/mosquitto/config
      - ./mosquitto/data:/mosquitto/data
      - ./mosquitto/log:/mosquitto/log

  api:
    build: ./api
    container_name: mec-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      - mosquitto
```

Commandes utiles :

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

---

## 10. Étape 6 — Définir les topics MQTT

Il faut standardiser les échanges dès le départ.

### Topics recommandés

```text
tsa/prediction
    -> le téléphone envoie un score de risque

tsa/fl/update
    -> le téléphone envoie une mise à jour FL

tsa/context/request
    -> le téléphone demande un contexte local

tsa/context/response/<client_id>
    -> le MEC renvoie le contexte local

tsa/recommendation/<client_id>
    -> le MEC renvoie une recommandation personnalisée

tsa/fl/global_model
    -> le MEC diffuse un modèle agrégé local
```

### Exemple de message `tsa/prediction`

```json
{
  "client_id": "pseudo_001",
  "zone": "station_A",
  "risk_score": 0.82,
  "timestamp": "2026-04-05T10:20:00Z"
}
```

### Exemple de message `tsa/fl/update`

```json
{
  "client_id": "pseudo_001",
  "model_version": "v1",
  "n_samples": 120,
  "weights": [0.12, -0.03, 0.98, 0.44],
  "timestamp": "2026-04-05T10:21:00Z"
}
```

---

## 11. Étape 7 — Développer l’API MEC

### 11.1 Rôle de l’API

L’API ne remplace pas MQTT. Elle sert à :

- vérifier l’état du MEC ;
- consulter la version du modèle global ;
- injecter ou simuler du contexte local ;
- faciliter les démonstrations.

### 11.2 Routes minimales

- `GET /status` : état général du MEC
- `GET /context` : contexte local actuel
- `POST /context` : modifier le contexte local pour les tests
- `GET /fl/model` : version et état du modèle agrégé
- `GET /metrics` : métriques simples

### 11.3 Exemple minimal FastAPI

Fichier `api/app.py` :

```python
from fastapi import FastAPI

app = FastAPI(title="MEC API")

CURRENT_CONTEXT = {
    "zone": "station_A",
    "noise": 0.4,
    "crowd": 0.6,
    "delay": 2
}

@app.get("/status")
def status():
    return {"status": "ok", "service": "mec-api"}

@app.get("/context")
def get_context():
    return CURRENT_CONTEXT
```

Fichier `api/requirements.txt` :

```text
fastapi
uvicorn[standard]
paho-mqtt
numpy
```

Fichier `api/Dockerfile` :

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 12. Étape 8 — Ajouter le service de contexte local

Le MEC doit être pertinent parce qu’il connaît le **contexte local de mobilité**.

### 12.1 Contexte simulé au départ

Variables locales possibles :

- `noise` : niveau sonore ;
- `crowd` : densité de foule ;
- `delay` : retard de transport ;
- `incident` : booléen ou type d’incident ;
- `safe_zone_available` : présence d’une zone calme.

### 12.2 Stratégie de prototype

Commencer avec un fichier JSON ou des valeurs injectées via l’API.

Exemple `context/context.json` :

```json
{
  "zone": "station_A",
  "noise": 0.8,
  "crowd": 0.9,
  "delay": 5,
  "safe_zone_available": true
}
```

### 12.3 Évolution possible

Ensuite, brancher ce service sur :

- une API transport ;
- des capteurs simulés ;
- un second script Python générant des événements.

---

## 13. Étape 9 — Implémenter la logique de recommandation MEC

Le MEC ne doit pas recalculer toute la biométrie. Il reçoit plutôt :

- le score individuel produit par le téléphone ;
- le contexte local.

### 13.1 Exemple de règle simple

```text
si risk_score > 0.7 ET crowd > 0.7
=> recommander une zone calme

si risk_score > 0.7 ET delay > 5
=> recommander une attente dans un espace moins bruyant
```

### 13.2 Exemple de pseudo-code

```python
def recommend(risk_score, context):
    if risk_score > 0.7 and context["crowd"] > 0.7:
        return "Diriger l'utilisateur vers une zone calme"
    if risk_score > 0.7 and context["delay"] > 5:
        return "Proposer d'attendre avant d'accéder au quai"
    return "Situation normale"
```

### 13.3 Objectif de cette étape

Montrer que le MEC apporte une vraie valeur :

- il ne voit pas les données brutes sensibles ;
- il reçoit un score minimal ;
- il ajoute de l’intelligence contextuelle locale.

---

## 14. Étape 10 — Implémenter l’agrégation FL locale

### 14.1 Rôle du MEC dans le FL

Le MEC joue ici le rôle d’**agrégateur local**.

Il reçoit les mises à jour de plusieurs téléphones d’une même zone, calcule un modèle local agrégé, puis :

- le redistribue localement ;
- ou l’envoie au backend pour une agrégation globale.

### 14.2 Algorithme de base : FedAvg

Si chaque téléphone envoie :

- `weights_i`
- `n_samples_i`

le MEC calcule :

```text
global_weight = somme(n_i * w_i) / somme(n_i)
```

### 14.3 Exemple Python simple

Fichier `fl/aggregator.py` :

```python
import numpy as np

def fedavg(updates):
    total_samples = sum(u["n_samples"] for u in updates)
    if total_samples == 0:
        raise ValueError("Aucun échantillon reçu")

    weighted_sum = None
    for u in updates:
        w = np.array(u["weights"], dtype=float)
        if weighted_sum is None:
            weighted_sum = u["n_samples"] * w
        else:
            weighted_sum += u["n_samples"] * w

    return (weighted_sum / total_samples).tolist()
```

### 14.4 Politique d’agrégation

Le MEC peut agréger :

- toutes les `N` mises à jour ;
- ou toutes les `X` secondes ;
- ou par zone.

Pour un premier prototype, prendre :

- agrégation toutes les 3 mises à jour.

### 14.5 Ce qu’il faut garder en mémoire

Le MEC ne reçoit pas les données brutes, seulement les **mises à jour du modèle local**.

---

## 15. Étape 11 — Publier le modèle agrégé

Une fois l’agrégation faite, le MEC publie sur un topic MQTT.

Exemple :

```json
{
  "model_version": "v2",
  "weights": [0.23, -0.02, 1.01, 0.39],
  "aggregated_from": 3,
  "timestamp": "2026-04-05T10:30:00Z"
}
```

Topic :

```text
tsa/fl/global_model
```

Les téléphones peuvent ensuite télécharger ce nouveau modèle et l’utiliser comme point de départ pour le prochain round fédéré.

---

## 16. Étape 12 — Ajouter un lien MEC → backend

Le backend central n’est pas obligatoire au tout début, mais il faut préparer l’interface.

### 16.1 Ce que le MEC enverra au backend

- modèle local agrégé ;
- numéro de version ;
- nombre de clients participants ;
- métriques d’agrégation.

### 16.2 Ce que le backend renverra au MEC

- nouveau modèle global ;
- version ;
- configuration ;
- seuils de décision.

### 16.3 Format recommandé

HTTPs JSON ou MQTTs, selon l’architecture globale choisie.

Pour le prototype, **HTTP REST** sera plus simple à déboguer.

---

## 17. Étape 13 — Sécuriser le MEC

Cette partie est essentielle car le sujet porte sur la vie privée.

### 17.1 Minimum à faire

- utiliser TLS pour MQTT ou HTTPS pour l’API ;
- pseudonymiser les identifiants ;
- ne pas stocker les données brutes utilisateurs ;
- limiter les logs.

### 17.2 Étapes progressives

#### Niveau 1 — Prototype rapide

- MQTT non chiffré sur réseau local ;
- pas d’authentification ;
- uniquement pour démonstration locale.

#### Niveau 2 — Version sérieuse du prototype

- TLS côté Mosquitto ;
- authentification utilisateur / mot de passe ;
- ACL sur les topics.

### 17.3 Exemple de sujet à documenter dans le rapport

- frontière de confiance ;
- type de données accepté par le MEC ;
- type de données explicitement refusé.

---

## 18. Étape 14 — Observabilité et debug

Il faut pouvoir démontrer simplement que le MEC fonctionne.

### À prévoir

- logs Docker ;
- logs Mosquitto ;
- endpoint `/status` ;
- affichage du dernier contexte ;
- affichage du dernier modèle agrégé ;
- scripts de test MQTT.

### Exemples de commandes utiles

```bash
docker compose logs -f mosquitto
docker compose logs -f api
curl http://localhost:8000/status
curl http://localhost:8000/context
```

---

## 19. Étape 15 — Scénario de démo minimal

### Démo 1 : communication simple

1. Démarrer le MEC.
2. Publier un message `tsa/prediction` depuis un client simulé.
3. Vérifier que le MEC reçoit le message.
4. Publier une recommandation sur `tsa/recommendation/<client_id>`.

### Démo 2 : contexte local

1. Modifier le contexte local via l’API.
2. Envoyer le même `risk_score`.
3. Montrer que la recommandation change selon l’affluence ou le bruit.

### Démo 3 : agrégation FL

1. Simuler 3 clients qui envoient des poids.
2. Le MEC agrège avec FedAvg.
3. Le MEC publie le nouveau modèle local agrégé.

---

## 20. Étape 16 — Plan de travail conseillé

### Semaine 1

- installer Docker ;
- vérifier `hello-world` ;
- installer Mosquitto ;
- tester `mosquitto_pub/sub`.

### Semaine 2

- créer `docker-compose.yml` ;
- déployer Mosquitto ;
- fixer les topics MQTT.

### Semaine 3

- créer l’API FastAPI ;
- ajouter `/status` et `/context`.

### Semaine 4

- implémenter le service de recommandation basé sur contexte local.

### Semaine 5

- implémenter la réception des mises à jour FL.

### Semaine 6

- coder FedAvg ;
- publier le modèle agrégé.

### Semaine 7

- ajouter le lien vers le backend ;
- préparer les métriques.

### Semaine 8

- sécuriser le broker ;
- documentation ;
- préparation de démo.

---

## 21. Livrables techniques attendus

À la fin, il faudrait idéalement avoir :

- un `docker-compose.yml` fonctionnel ;
- un broker Mosquitto opérationnel ;
- une API MEC fonctionnelle ;
- un script de recommandation MEC ;
- un agrégateur FL local `FedAvg` ;
- une documentation expliquant les flux de données ;
- un scénario de démo reproductible.

---

## 22. Check-list finale

### Installation

- [ ] Docker installé
- [ ] Docker démarré
- [ ] utilisateur ajouté au groupe docker
- [ ] Mosquitto lancé en conteneur
- [ ] tests `mosquitto_pub/sub` validés

### Services MEC

- [ ] API FastAPI opérationnelle
- [ ] service de contexte local opérationnel
- [ ] logique de recommandation opérationnelle
- [ ] agrégateur FL opérationnel

### Sécurité et confidentialité

- [ ] aucune donnée brute stockée sur le MEC
- [ ] identifiants pseudonymisés
- [ ] plan de passage à TLS documenté

### Démo

- [ ] réception d’une prédiction téléphone
- [ ] réponse MEC dépendant du contexte
- [ ] agrégation de plusieurs mises à jour FL
- [ ] publication d’un modèle agrégé

---

## 23. Conseils de réussite

1. **Ne commence pas par le FL** : commence par Docker + Mosquitto + échange simple.
2. **Valide chaque brique indépendamment** avant d’empiler le reste.
3. **Conserve une architecture simple** : communication, contexte, décision, puis agrégation.
4. **Documente les flux de données** dès le départ, car c’est central pour le sujet privacy.
5. **Pense démonstration** : il faut que ton encadrant puisse voir rapidement ce que fait le MEC.

---

## 24. Résumé en une phrase

Le MEC de ce projet est un **serveur local conteneurisé** qui reçoit des informations minimales venant des téléphones, intègre un contexte de mobilité local, produit des recommandations rapides et agrège les mises à jour issues de l’apprentissage fédéré sans manipuler les données brutes sensibles.

