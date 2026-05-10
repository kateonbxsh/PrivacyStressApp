# Federated Server Prototype (Flower + PyTorch)

## Project Context

This folder is the **machine learning module** of the group repository.
It contains a minimal technical prototype for a Federated Learning (FL) workflow.
It is designed to validate a complete local FL pipeline before integration into a larger privacy-preserving mobility project.

This is **not** the final product. It is an educational/technical baseline using synthetic data.

## What This Prototype Includes

- A Flower `ServerApp`
- A Flower `ClientApp`
- Three PyTorch model roles:
  - `PhoneModel`: trained locally on each phone
  - `MECModel`: trained at the edge on aggregate non-identifying summaries
  - `GlobalModel`: aggregated by the central Flower server
- Synthetic data split across 2 simulated clients
- Basic privacy protection on client updates: clipping + Gaussian noise

The goal is to validate:
1. Global parameter initialization
2. Local client training
3. Server-side aggregation (FedAvg)
4. Federated evaluation
5. A clean separation between phone, MEC, and global model responsibilities

## Privacy-First Architecture

```text
Phone
  - stores raw sensitive answers/preferences locally
  - trains PhoneModel on local data
  - sends only clipped/noised model updates
  - exposes only coarse training metrics

MEC / edge node
  - receives no raw questionnaire data
  - trains MECModel on aggregate summaries
  - can support local adaptation close to the user

Global server
  - runs Flower FedAvg
  - updates GlobalModel from client model updates
  - never needs direct access to user records
```

## Tech Stack

- Python `>=3.12,<3.14`
- Poetry
- Flower `>=1.27,<2.0`
- PyTorch
- NumPy

## Repository Structure

```text
app/
  server_app.py   # Flower server setup (strategy, rounds, server config)
  client_app.py   # Flower NumPyClient implementation (fit/evaluate)
  task.py         # Synthetic phone data, train/evaluate helpers
  models.py       # PhoneModel, MECModel, GlobalModel
  privacy.py      # Update clipping/noising and safe public metrics
  edge.py         # MEC-side synthetic summary example
pyproject.toml    # Poetry dependencies and Flower app component entry points
poetry.lock       # Locked dependency versions
```

## Installation

### 1) Open the ML folder

```bash
cd /mnt/c/Users/pc/Desktop/PrivacyStressApp/ml
```

### 2) Configure Poetry to use an in-project virtual environment

```bash
poetry config virtualenvs.in-project true
```

### 3) Install dependencies

```bash
poetry install
```

## Run the Local Simulation

```bash
poetry run flwr run . --stream
```

If Flower tries to use an invalid Windows-like path such as `C:Userspc/.flwr`, run it with an explicit Flower home:

```bash
rm -rf /tmp/flwr-yatsu

FLWR_HOME=/tmp/flwr-yatsu \
HOME=/home/yatsu \
poetry run flwr run . --stream \
  --federation-config num-supernodes=2 \
  --federation-config client-resources-num-cpus=1 \
  --federation-config init-args-num-cpus=1
```

Expected output includes:
- `Starting Flower Simulation`
- `[ROUND 1]`, `[ROUND 2]`, `[ROUND 3]`
- `[SUMMARY]` with distributed loss history

## Troubleshooting

### 1) `Import "flwr..." could not be resolved` (or `ModuleNotFoundError`)

Cause:
- Dependencies are not installed in the Poetry environment, or your IDE is using a different interpreter.

Fix:
```bash
poetry install
poetry run python -c "import flwr; print(flwr.__version__)"
```

### 2) Python / PyTorch / Triton compatibility issues

Cause:
- Using an unsupported Python version can break PyTorch/Triton and simulation runtime behavior.

Fix:
- Use Python `>=3.12,<3.14` as defined in `pyproject.toml`.
- Recreate the Poetry environment with a compatible Python if needed.

### 3) VS Code not using the Poetry interpreter

Symptoms:
- Imports fail in editor, but commands work in terminal.

Fix:
1. Open Command Palette: `Python: Select Interpreter`
2. Select `.venv/bin/python` from this repository

### 4) Flower FAB build issues due to large local files

Cause:
- If `.venv` is not ignored, Flower packaging/scanning can become slow or fail due to oversized bundles.

Fix:
- Keep `.venv/` in `.gitignore`
- Avoid committing local build/cache directories

### 5) Local SuperLink startup issues

Symptoms:
- Timeouts or local simulation not starting cleanly.

Fix:
- Run with streaming logs:
```bash
poetry run flwr run . --stream
```
- Check local Flower logs under:
`~/.flwr/local-superlink/`
