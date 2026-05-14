# MEC Layer

This folder contains the regional Mobile Edge Computing layer used by the PrivacyStressApp prototype.

It is intentionally directly under `mec/` now. The old `mes/pir-mec` nesting has been removed so the edge stack is easy to find and run.

## Role In The Architecture

The MEC layer is the intermediate AI layer between phones and the cloud:

- receives only phone model updates, risk scores, or pseudonymous context requests
- aggregates nearby device updates with FedAvg
- specializes behavior to regional mobility conditions such as crowding, delays, local noise, infrastructure state, and weather-like context
- publishes regional model weights back to devices
- forwards only aggregate metadata to the cloud backend through `POST /api/federated/updates`

The MEC must not receive raw ASD questionnaire answers, raw physiological histories, or precise personal mobility traces.

## Files

- `docker-compose.yml`: starts the regional stack
- `api/`: FastAPI status and local context API
- `context/`: MQTT recommendation service using local mobility context
- `fl/`: regional federated aggregation service
- `mosquitto/`: MQTT broker configuration
- `scripts/`: phone and environment simulation scripts
- `TOPICS.md`: MQTT topic contract
- `DOCKER_DEMO.md`: manual demo flow

## Run

From the repository root, the easiest path is:

```powershell
.\run_project.ps1
```

To run only the MEC layer:

```bash
cd mec
docker compose up --build
```

The MEC API will be available at `http://localhost:8000/status`.

## Demo Flow

1. Start backend and UI from the project root with `.\run_project.ps1`.
2. Start or keep the MEC stack running through Docker Compose.
3. Run `scripts/simulate_phone.py` to publish local phone predictions and federated updates.
4. Run `scripts/demo_control.py` to change local context such as crowd, noise, and delay.
5. Watch the MEC FL service aggregate phone updates and synchronize aggregate metadata to the backend cloud API.

## Hierarchical Federated Learning Flow

```text
Phone local model
  - real-time inference
  - local personalization and feedback learning
  - sends only protected parameter updates

MEC regional model
  - receives nearby updates
  - performs regional FedAvg
  - adapts to local transport/context patterns
  - forwards only aggregate metadata to backend

Cloud global model
  - receives MEC-level aggregate updates
  - tracks global model versions and analytics
  - redistributes improved initialization metadata
```
