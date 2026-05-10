from __future__ import annotations

import torch
from torch.utils.data import DataLoader, TensorDataset

from .models import get_mec_model
from .task import evaluate, train


def build_edge_summary(features: torch.Tensor) -> torch.Tensor:
    """Create MEC inputs from aggregate feature statistics only."""
    return torch.stack(
        [
            features[:, 0].mean(),
            features[:, 1].mean(),
            features[:, 2].mean(),
            features[:, 3:].mean(),
        ]
    )


def simulate_mec_training() -> dict[str, float]:
    """Small standalone MEC example on non-identifying synthetic summaries."""
    summaries = torch.tensor(
        [
            [0.20, 0.10, 0.70, 0.30],
            [0.80, 0.70, 0.20, 0.60],
            [0.35, 0.25, 0.65, 0.40],
            [0.75, 0.85, 0.15, 0.70],
        ],
        dtype=torch.float32,
    )
    labels = torch.tensor([0, 1, 0, 1], dtype=torch.long)

    loader = DataLoader(TensorDataset(summaries, labels), batch_size=2, shuffle=True)
    model = get_mec_model()
    loss, examples = train(model, loader, epochs=5)
    val_loss, _, accuracy = evaluate(model, loader)

    return {
        "train_loss": float(loss),
        "val_loss": float(val_loss),
        "accuracy": float(accuracy),
        "examples": float(examples),
    }
