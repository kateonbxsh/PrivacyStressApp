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
