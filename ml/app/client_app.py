from __future__ import annotations

from flwr.client import ClientApp, NumPyClient
from flwr.common import Context

from .models import get_phone_model
from .personalized import train_personalized_components, zero_like_parameters
from .privacy import clip_and_noise_update, public_training_metrics
from .task import (
    evaluate,
    load_data,
    set_parameters,
)


def state_to_parameters(state):
    return [value.detach().cpu().numpy() for value in state.values()]


class FlowerClient(NumPyClient):
    """Minimal simulated Flower client."""

    def __init__(self, partition_id: int) -> None:
        self.partition_id = partition_id
        self.model = get_phone_model()
        self.personal_state = zero_like_parameters(self.model)
        self.trainloader, self.valloader = load_data(partition_id)

    def get_parameters(self, config):
        return get_parameters(self.model)

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)
        shared_state = self.model.state_dict()
        before = state_to_parameters(shared_state)
        local_epochs = int(config.get("local_epochs", 1))
        loss, num_examples = train_personalized_components(
            model=self.model,
            shared_state=shared_state,
            personal_state=self.personal_state,
            trainloader=self.trainloader,
            epochs=local_epochs,
            shared_lr=float(config.get("shared_lr", 0.05)),
            personal_lr=float(config.get("personal_lr", 0.1)),
        )
        after = state_to_parameters(shared_state)

        shared_parameters_only = clip_and_noise_update(
            before=before,
            after=after,
            clipping_norm=float(config.get("clipping_norm", 1.0)),
            noise_std=float(config.get("noise_std", 0.01)),
        )
        metrics = public_training_metrics(loss)
        metrics["personal_component_sent"] = 0.0
        metrics["model_decomposition"] = "wi=ws+vi"
        return shared_parameters_only, num_examples, metrics

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
