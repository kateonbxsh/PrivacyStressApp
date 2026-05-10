from fastapi import FastAPI

app = FastAPI(title="MEC API")

# Simulation d'un contexte local par défaut
# Ces données seront utilisées pour influencer les recommandations
CURRENT_CONTEXT = {
    "zone": "station_A",
    "noise": 0.4, # Niveau de bruit de 0 à 1
    "crowd": 0.6, # Densité de foule de 0 à 1
    "delay": 2    # Retard en minutes
}

@app.get("/status")
def status():
    """Vérifie si le service MEC est opérationnel."""
    return {"status": "ok", "service": "mec-api"}

@app.get("/context")
def get_context():
    """Récupère le contexte local actuel du MEC."""
    return CURRENT_CONTEXT

@app.post("/context/update")
def update_context(new_context: dict):
    """Permet de mettre à jour le contexte (utile pour les tests/simulations)."""
    global CURRENT_CONTEXT
    CURRENT_CONTEXT.update(new_context)
    return {"message": "Contexte mis à jour", "new_context": CURRENT_CONTEXT}
