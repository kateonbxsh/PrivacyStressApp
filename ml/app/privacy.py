from __future__ import annotations

import numpy as np


def clip_and_noise_update(
    before: list[np.ndarray],
    after: list[np.ndarray],
    clipping_norm: float,
    noise_std: float,
) -> list[np.ndarray]:
    """Return parameters after clipping and noising the local model update."""
    updates = [new - old for old, new in zip(before, after)]
    total_norm = float(np.sqrt(sum(np.sum(update**2) for update in updates)))

    if clipping_norm > 0 and total_norm > clipping_norm:
        scale = clipping_norm / (total_norm + 1e-12)
        updates = [update * scale for update in updates]

    if noise_std > 0:
        updates = [
            update + np.random.normal(0.0, noise_std, size=update.shape).astype(update.dtype)
            for update in updates
        ]

    return [old + update for old, update in zip(before, updates)]


def public_training_metrics(loss: float) -> dict[str, float]:
    """Expose only coarse non-sensitive metrics to the server logs."""
    return {
        "train_loss": round(float(loss), 4),
    }
