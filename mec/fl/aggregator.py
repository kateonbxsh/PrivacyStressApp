import numpy as np


def _extract_shared_weights(update):
    if "personal_weights" in update or "personal_update" in update:
        raise ValueError("Personal adaptation vi must never be sent to the MEC")

    weights = update.get("shared_weights") or update.get("sharedWeights")
    if weights is None:
        raise ValueError("MEC aggregation requires shared_weights/sharedWeights")

    return np.array(weights, dtype=float)


def fedavg(updates):
    """Aggregate only shared phone components ws_i.

    Phones use wi = ws + vi locally, but the MEC must only receive and
    aggregate ws updates. The private vi component stays on the phone.
    """
    if not updates:
        return None

    total_samples = sum(int(update["n_samples"]) for update in updates)
    if total_samples == 0:
        return None

    weighted_sum = None
    for update in updates:
        shared_weights = _extract_shared_weights(update)
        contribution = int(update["n_samples"]) * shared_weights
        weighted_sum = contribution if weighted_sum is None else weighted_sum + contribution

    return (weighted_sum / total_samples).tolist()
