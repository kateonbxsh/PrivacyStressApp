import os
import time

import requests
from fastapi import FastAPI

app = FastAPI(title="MEC API")

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://host.docker.internal:4000/api").rstrip("/")
MEC_NODE_NAME = os.getenv("MEC_NODE_NAME", "MEC Local Docker")
MEC_REGION = os.getenv("MEC_REGION", "local-demo")
DEFAULT_SHARED_WEIGHTS = [0.18, 0.22, 0.2, 0.16, 0.12, 0.14, 0.1, 0.12, -0.55]

CURRENT_CONTEXT = {
    "zone": "station_A",
    "noise": 0.4,
    "crowd": 0.6,
    "delay": 2,
}

REGIONAL_MODEL = {
    "scope": "mec",
    "name": MEC_NODE_NAME,
    "region": MEC_REGION,
    "version": "mec-local-v0",
    "sharedWeights": DEFAULT_SHARED_WEIGHTS,
    "sampleCount": 0,
    "personalComponent": "never_stored_on_mec",
}


def initialize_from_cloud():
    try:
        response = requests.get(
            f"{BACKEND_API_URL}/federated/regional-model",
            params={"region": MEC_REGION, "mecNodeName": MEC_NODE_NAME},
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        REGIONAL_MODEL.update(
            {
                "version": body.get("version", REGIONAL_MODEL["version"]),
                "sharedWeights": body.get("sharedWeights", REGIONAL_MODEL["sharedWeights"]),
                "sampleCount": body.get("sampleCount", 0),
                "initializedFrom": body.get("initializedFrom", "cloud"),
            }
        )
    except Exception:
        REGIONAL_MODEL["initializedFrom"] = "local_default"


initialize_from_cloud()


@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": "mec-api",
        "mecNodeName": MEC_NODE_NAME,
        "region": MEC_REGION,
        "modelVersion": REGIONAL_MODEL["version"],
    }


@app.get("/context")
def get_context():
    return CURRENT_CONTEXT


@app.post("/context/update")
def update_context(new_context: dict):
    CURRENT_CONTEXT.update(new_context)
    return {"message": "Context updated", "new_context": CURRENT_CONTEXT}


@app.get("/fl/model")
def get_fl_model():
    """Phones initialize their shared component ws from this regional MEC model."""
    return REGIONAL_MODEL


@app.post("/fl/model")
def update_fl_model(model_update: dict):
    """The MEC FL service updates only the regional shared component ws."""
    shared_weights = model_update.get("sharedWeights")
    if not isinstance(shared_weights, list):
        return {"ok": False, "error": "sharedWeights must be a list"}

    REGIONAL_MODEL.update(
        {
            "version": model_update.get("version", f"mec-r{int(time.time())}"),
            "sharedWeights": shared_weights,
            "sampleCount": int(model_update.get("sampleCount", REGIONAL_MODEL["sampleCount"])),
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )
    return {"ok": True, "model": REGIONAL_MODEL}
