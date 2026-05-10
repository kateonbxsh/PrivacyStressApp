from __future__ import annotations

from flwr.client import ClientApp, NumPyClient
from flwr.common import Context

from .models import get_phone_model
from .privacy import clip_and_noise_update, public_training_metrics
from .task import (
    evaluate,
    get_parameters,
    load_data,
    set_parameters,
    train,
)


class FlowerClient(NumPyClient):
    """Minimal simulated Flower client."""

    def __init__(self, partition_id: int) -> None:
        self.partition_id = partition_id
        self.model = get_phone_model()
        self.trainloader, self.valloader = load_data(partition_id)

    def get_parameters(self, config):
        return get_parameters(self.model)

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)
        before = get_parameters(self.model)
        local_epochs = int(config.get("local_epochs", 1))
        loss, num_examples = train(self.model, self.trainloader, epochs=local_epochs)
        after = get_parameters(self.model)

        private_parameters = clip_and_noise_update(
            before=before,
            after=after,
            clipping_norm=float(config.get("clipping_norm", 1.0)),
            noise_std=float(config.get("noise_std", 0.01)),
        )
        metrics = public_training_metrics(loss)
        return private_parameters, num_examples, metrics

    def evaluate(self, parameters, config):
        set_parameters(self.model, parameters)
        loss, num_examples, accuracy = evaluate(self.model, self.valloader)

        metrics = {
            "accuracy": float(accuracy),
        }
        return float(loss), num_examples, metrics


def client_fn(context: Context):
    """Create one client from Flower runtime context."""
    partition_id = int(context.node_config["partition-id"])
    return FlowerClient(partition_id).to_client()


app = ClientApp(client_fn=client_fn)
