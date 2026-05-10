from __future__ import annotations

from collections import OrderedDict

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from .models import GlobalModel, get_global_model


def get_model() -> GlobalModel:
    """Create the global model used as the FedAvg reference."""
    return get_global_model()


def get_parameters(model: nn.Module) -> list:
    """Return model parameters as NumPy arrays."""
    return [val.detach().cpu().numpy() for _, val in model.state_dict().items()]


def set_parameters(model: nn.Module, parameters: list) -> None:
    """Load NumPy parameters into the model."""
    params_dict = zip(model.state_dict().keys(), parameters)
    state_dict = OrderedDict({key: torch.tensor(value) for key, value in params_dict})
    model.load_state_dict(state_dict, strict=True)


def load_data(partition_id: int) -> tuple[DataLoader, DataLoader]:
    """Create synthetic private phone data for one simulated client."""
    if partition_id == 0:
        x_train = torch.tensor(
            [
                [0.10, 0.20, 0.80, 0.30, 0.10, 0.40],
                [0.20, 0.10, 0.70, 0.20, 0.20, 0.30],
                [0.80, 0.75, 0.20, 0.60, 0.70, 0.90],
            ],
            dtype=torch.float32,
        )
        y_train = torch.tensor([0, 0, 1], dtype=torch.long)

        x_val = torch.tensor(
            [
                [0.90, 0.80, 0.10, 0.70, 0.60, 0.80],
                [0.15, 0.20, 0.85, 0.20, 0.10, 0.30],
            ],
            dtype=torch.float32,
        )
        y_val = torch.tensor([1, 0], dtype=torch.long)
    else:
        x_train = torch.tensor(
            [
                [0.85, 0.70, 0.15, 0.80, 0.60, 0.75],
                [0.75, 0.80, 0.25, 0.70, 0.80, 0.60],
                [0.25, 0.15, 0.75, 0.30, 0.20, 0.35],
            ],
            dtype=torch.float32,
        )
        y_train = torch.tensor([1, 1, 0], dtype=torch.long)

        x_val = torch.tensor(
            [
                [0.20, 0.10, 0.80, 0.20, 0.20, 0.40],
                [0.90, 0.85, 0.10, 0.80, 0.70, 0.90],
            ],
            dtype=torch.float32,
        )
        y_val = torch.tensor([0, 1], dtype=torch.long)

    trainset = TensorDataset(x_train, y_train)
    valset = TensorDataset(x_val, y_val)

    trainloader = DataLoader(trainset, batch_size=2, shuffle=True)
    valloader = DataLoader(valset, batch_size=2, shuffle=False)
    return trainloader, valloader


def train(model: nn.Module, trainloader: DataLoader, epochs: int) -> tuple[float, int]:
    """Train locally for a few epochs and return average loss and sample count."""
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

    model.train()
    total_loss = 0.0
    total_examples = 0

    for _ in range(epochs):
        for features, labels in trainloader:
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            batch_size = labels.size(0)
            total_loss += loss.item() * batch_size
            total_examples += batch_size

    avg_loss = total_loss / total_examples if total_examples else 0.0
    return avg_loss, total_examples


def evaluate(model: nn.Module, valloader: DataLoader) -> tuple[float, int, float]:
    """Evaluate the model and return loss, sample count, and accuracy."""
    criterion = nn.CrossEntropyLoss()
    model.eval()

    total_loss = 0.0
    total_examples = 0
    total_correct = 0

    with torch.no_grad():
        for features, labels in valloader:
            outputs = model(features)
            loss = criterion(outputs, labels)

            predictions = torch.argmax(outputs, dim=1)
            total_correct += (predictions == labels).sum().item()

            batch_size = labels.size(0)
            total_loss += loss.item() * batch_size
            total_examples += batch_size

    avg_loss = total_loss / total_examples if total_examples else 0.0
    accuracy = total_correct / total_examples if total_examples else 0.0
    return avg_loss, total_examples, accuracy
