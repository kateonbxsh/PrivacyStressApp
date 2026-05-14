# PrivacyStressApp / NeuroMove

Operational research prototype for privacy-preserving smart mobility support for people with Autism Spectrum Disorder (ASD).

The project is now organized as one coherent vertical slice:

- `backend`: Express + Prisma + SQLite API for session auth, encrypted ASD profile recovery, privacy-preserving check-in storage, admin analytics, MEC node status, and federated update metadata.
- `ui`: NiceGUI web app for login, onboarding, check-ins, activity, settings, and admin/research dashboards.
- `ml`: Flower/PyTorch federated learning prototype with phone, MEC, and global model roles.
- `mec`: Dockerized MEC/MQTT simulation for local context, regional FedAvg aggregation, and cloud synchronization metadata.

## Architecture

```text
Cloud backend / global AI layer
  - encrypted profile sync
  - global analytics and federated update metadata
  - receives only aggregated MEC model-update summaries
  - redistributes global initialization/version metadata

MEC / regional AI layer
  - local context simulation
  - regional FedAvg aggregation from nearby devices
  - region-specific mobility adaptation
  - node health and model version metadata
  - forwards higher-level aggregate updates to the cloud backend

Device / local AI layer
  - ASD profile recovery after login
  - contextual check-in
  - local-style stress inference
  - future local fine-tuning on feedback
  - sends only encrypted/noised federated updates to MEC
```

Raw questionnaire vectors are protected as encrypted transformed vectors. Check-ins sent to the backend are reduced to derived metrics and predictions; raw contextual payloads are not persisted in `CheckIn`.

## Personalized Federated Learning

The phone model is decomposed as:

```text
wi = ws + vi
```

- `ws`: shared component initialized from the current MEC regional model
- `vi`: personal adaptation component initialized to zero and stored only on the phone/UI session
- `wi`: effective model used for phone-local inference

During local phone training:

```text
ws <- ws - eta_s grad Li(ws + vi)
vi <- vi - eta_p grad Li(ws + vi)
```

Only `ws` is sent to the MEC through the MQTT topic `tsa/fl/update`. The personal component `vi` is never sent to MEC or cloud.

The MEC aggregates only shared components:

```text
ws_region <- sum_i (ni / N) * ws_i
```

The cloud backend aggregates only regional shared models submitted by MEC nodes. New MEC nodes initialize from the cloud global shared model. New phones initialize from their current MEC shared model. If a phone switches region, for example Toulouse to Paris, only `ws_toulouse` is replaced by `ws_paris`; the phone preserves `vi`, so the new effective model is:

```text
wi = ws_paris + vi
```

## Run Everything

From the project root:

```powershell
.\run_project.ps1 -Setup
```

Later runs can skip setup:

```powershell
.\run_project.ps1
```

The runner starts:

- backend cloud API on `http://localhost:4000`
- web UI on `http://localhost:8080`
- MEC Docker stack on `http://localhost:8000` when Docker is available

Use `.\run_project.ps1 -SkipMec` to run only backend and UI, or `.\run_project.ps1 -WithMl` to also launch the Flower ML simulation when Poetry is installed.

## Backend

```powershell
cd backend
pnpm install
bunx prisma generate
bunx prisma db push
bun src/index.ts
```

The backend reads `backend/.env`. Demo users are seeded by default:

- `demo@neuromove.app / demo12345`
- `research@neuromove.app / research123`
- `admin@neuromove.app / admin12345`

Important endpoints:

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/auth/session`
- `POST /api/checkins`
- `GET /api/checkins`
- `GET /api/admin/dashboard`
- `POST /api/federated/updates`
- `GET /api/federated/global-model`
- `GET /api/federated/regional-model?region=local-demo&mecNodeName=MEC%20Local%20Docker`
- `GET /api/docs`

## UI

```powershell
cd ui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:API_BASE_URL="http://localhost:4000/api"
$env:USE_MOCK_API="false"
$env:USE_MOCK_ADMIN_ANALYTICS="false"
python -m app.main
```

Open `http://localhost:8080`.

If the backend is unavailable, selected UI flows fall back to local mock behavior so the interface remains demonstrable.

## MEC Simulation

```bash
cd mec
docker compose up --build
```

This starts Mosquitto, the MEC API, context service, and FL aggregation service. See `mec/README.md` and `mec/DOCKER_DEMO.md`.

## ML Simulation

```bash
cd ml
poetry install
poetry run flwr run . --stream
```

The ML module is still a synthetic Flower baseline. The backend now exposes the integration point where future trained clients/MEC nodes can report accepted update metadata.

## Smoke Test

After starting the backend:

```powershell
$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-RestMethod http://localhost:4000/api/auth/login -Method Post -ContentType 'application/json' -Body '{"email":"demo@neuromove.app","password":"demo12345"}' -WebSession $s
Invoke-RestMethod http://localhost:4000/api/checkins -Method Post -ContentType 'application/json' -Body '{"timestamp":"2026-05-14T10:00:00.000Z","source":"manual_checkin","user_context":{"energy_level":3,"breathing_state":"normal","physical_discomfort":0,"speaking_difficulty":"none","need_isolation":"no"},"environment":{"noise_level":3,"light_level":"bright","crowd_density":"medium","routine_disruption":"none","transition_difficulty":"light","social_load":"moderate","calm_space_available":"yes"},"sensor_data":{"heart_rate":92,"has_wearable":false,"hrv":null,"sleep_quality":3},"mobility_context":{"transport_mode":"metro","transport_difficulty":"light"},"observable_signs":{"pacing_agitation":false,"increased_stimming":false,"shutdown_signs":false}}' -WebSession $s
```
