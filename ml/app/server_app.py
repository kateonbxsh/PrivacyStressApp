from __future__ import annotations

from flwr.common import Context
from flwr.common import ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg

from .models import get_global_model
from .task import get_parameters


def fit_config(server_round: int) -> dict[str, int | float]:
    """Send per-round config to clients."""
    _ = server_round
    return {
        "local_epochs": 1,
        "clipping_norm": 1.0,
        "noise_std": 0.01,
    }


def server_fn(context: Context) -> ServerAppComponents:
    """Configure the federated server strategy."""
    num_rounds = 3
    initial_parameters = ndarrays_to_parameters(get_parameters(get_global_model()))

    strategy = FedAvg(
        fraction_fit=0.5,
        fraction_evaluate=0.5,
        min_fit_clients=1,
        min_evaluate_clients=1,
        min_available_clients=1,
        on_fit_config_fn=fit_config,
        initial_parameters=initial_parameters,
    )

    return ServerAppComponents(
        strategy=strategy,
        config=ServerConfig(num_rounds=num_rounds, round_timeout=120.0),
    )


app = ServerApp(server_fn=server_fn)
