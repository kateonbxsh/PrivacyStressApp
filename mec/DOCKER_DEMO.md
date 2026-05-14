# MEC Docker Demo

This demo shows the regional AI layer working between simulated phones and the cloud backend.

## 1. Start The Full Project

From the repository root:

```powershell
.\run_project.ps1
```

This starts the backend cloud API, the UI, and the MEC Docker stack when Docker is available.

## 2. Start The MEC Stack Only

```bash
cd mec
docker compose up --build
```

Watch the `mec-fl` logs. It receives model weights, aggregates them with FedAvg, publishes the regional model, and tries to notify the backend cloud API.

## 3. Simulate Phones

In another terminal:

```bash
cd mec
python scripts/simulate_phone.py
```

Run the same command in multiple terminals to simulate several nearby devices. Aggregation is triggered after three local updates by default.

## 4. Simulate Local Mobility Conditions

In another terminal:

```bash
cd mec
python scripts/demo_control.py
```

This changes regional context such as noise, crowding, and delay. The context service uses those values to adjust recommendations without receiving raw personal data.

## What To Show

- Device privacy: phones publish stress scores and model weights, not raw heart-rate histories or ASD survey answers.
- Regional adaptation: MEC recommendations change when local conditions change.
- Hierarchical FL: phones send updates to MEC, MEC performs regional FedAvg, then MEC sends aggregate metadata to the cloud backend.
