from __future__ import annotations

from collections import OrderedDict

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


def zero_like_parameters(model: nn.Module) -> OrderedDict[str, torch.Tensor]:
    return OrderedDict((name, torch.zeros_like(value)) for name, value in model.state_dict().items())


def load_effective_parameters(model: nn.Module, shared_state, personal_state) -> None:
    effective = OrderedDict(
        (name, shared_state[name] + personal_state[name])
        for name in shared_state.keys()
    )
    model.load_state_dict(effective, strict=True)


def train_personalized_components(
    model: nn.Module,
    shared_state,
    personal_state,
    trainloader: DataLoader,
    epochs: int,
    shared_lr: float,
    personal_lr: float,
) -> tuple[float, int]:
    """Train ws and vi locally, returning only public metrics.

    Effective phone model: wi = ws + vi.
    Gradients are computed on wi, then applied separately:
    ws <- ws - eta_s grad Li(wi)
    vi <- vi - eta_p grad Li(wi)
    """
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    total_examples = 0

    for _ in range(epochs):
        for features, labels in trainloader:
            load_effective_parameters(model, shared_state, personal_state)
            model.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()

            with torch.no_grad():
                for name, parameter in model.named_parameters():
                    if parameter.grad is None:
                        continue
                    shared_state[name] -= shared_lr * parameter.grad
                    personal_state[name] -= personal_lr * parameter.grad

            batch_size = labels.size(0)
            total_loss += loss.item() * batch_size
            total_examples += batch_size

    load_effective_parameters(model, shared_state, personal_state)
    avg_loss = total_loss / total_examples if total_examples else 0.0
    return avg_loss, total_examples
