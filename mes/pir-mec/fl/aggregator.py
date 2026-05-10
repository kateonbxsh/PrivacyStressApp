import numpy as np

def fedavg(updates):
    """
    Implémente l'algorithme Federated Averaging (FedAvg).
    
    Args:
        updates (list): Liste de dictionnaires contenant 'weights' (list) et 'n_samples' (int).
        
    Returns:
        list: Les poids agrégés.
    """
    if not updates:
        return None

    total_samples = sum(u["n_samples"] for u in updates)
    if total_samples == 0:
        return None

    weighted_sum = None
    
    for u in updates:
        w = np.array(u["weights"], dtype=float)
        if weighted_sum is None:
            weighted_sum = u["n_samples"] * w
        else:
            weighted_sum += u["n_samples"] * w

    # Calcul de la moyenne pondérée
    aggregated_weights = weighted_sum / total_samples
    
    return aggregated_weights.tolist()
