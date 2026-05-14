# Standards de communication MQTT pour le projet PIR TSA

Ce document définit les canaux (topics) et le format des messages échangés entre les téléphones et le MEC.

## 1. Score de Stress (Téléphone -> MEC)
**Topic** : `tsa/prediction`
**Format JSON** :
```json
{
  "client_id": "user_123",
  "risk_score": 0.85,
  "timestamp": "2026-04-05T12:00:00Z"
}
```

## 2. Requête de Contexte (Téléphone -> MEC)
**Topic** : `tsa/context/request`
**Format JSON** :
```json
{
  "client_id": "user_123",
  "zone": "station_A"
}
```

## 3. Réponse de Contexte (MEC -> Téléphone)
**Topic** : `tsa/context/response/user_123`
**Format JSON** :
```json
{
  "zone": "station_A",
  "noise": 0.2,
  "crowd": 0.9,
  "delay": 5
}
```

## 4. Recommandation (MEC -> Téléphone)
**Topic** : `tsa/recommendation/user_123`
**Format JSON** :
```json
{
  "message": "Foule dense détectée. Dirigez-vous vers la zone de repos B.",
  "level": "warning"
}
```

## 5. Personalized Federated Learning Update (Téléphone -> MEC)

Topic:

```text
tsa/fl/update
```

Payload:

```json
{
  "client_id": "pseudo_001",
  "shared_weights": [0.18, 0.22, 0.2, 0.16, 0.12, 0.14, 0.1, 0.12, -0.55],
  "n_samples": 32,
  "timestamp": 1778768000.0,
  "personal_component_included": false
}
```

The phone effective model is `wi = ws + vi`, but only `ws` is published. The personal adaptation component `vi` must remain on the phone.

## 6. Regional Shared Model (MEC -> Téléphone)

Topic:

```text
tsa/fl/global_model
```

Payload:

```json
{
  "model_version": "mec-r1778768000",
  "sharedWeights": [0.19, 0.21, 0.2, 0.17, 0.12, 0.13, 0.1, 0.12, -0.52],
  "aggregated_from": 3,
  "mec_node": "MEC Local Docker",
  "region": "local-demo"
}
```

When this arrives after a region switch or MEC update, the phone replaces only `ws` and preserves `vi`.
