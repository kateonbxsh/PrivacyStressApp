from __future__ import annotations

import torch
import torch.nn as nn


PHONE_INPUT_DIM = 6
MEC_SUMMARY_DIM = 4
NUM_CLASSES = 2


class MobilityTsaNet(nn.Module):
    """Shared architecture for phone-side training and global aggregation."""

    def __init__(self, input_dim: int = PHONE_INPUT_DIM, hidden_dim: int = 12) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, NUM_CLASSES),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class PhoneModel(MobilityTsaNet):
    """Model trained locally on the phone with private user data."""


class GlobalModel(MobilityTsaNet):
    """Server-side model receiving only federated parameter updates."""


class MECModel(nn.Module):
    """Edge model using privacy-preserving summaries, not raw phone records."""

    def __init__(self, input_dim: int = MEC_SUMMARY_DIM, hidden_dim: int = 8) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, NUM_CLASSES),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


def get_phone_model() -> PhoneModel:
    return PhoneModel()


def get_global_model() -> GlobalModel:
    return GlobalModel()


def get_mec_model() -> MECModel:
    return MECModel()
