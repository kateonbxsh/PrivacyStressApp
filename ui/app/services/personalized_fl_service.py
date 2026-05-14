from __future__ import annotations

import math
import json
import time
from typing import Any

import httpx
from nicegui import app

from app.core.config import (
    API_BASE_URL,
    MEC_API_URL,
    MEC_NODE_NAME,
    MEC_REGION,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
)
from app.core.session import get_current_user

DEFAULT_SHARED_WEIGHTS = [0.18, 0.22, 0.2, 0.16, 0.12, 0.14, 0.1, 0.12, -0.55]
LOCAL_SHARED_LR = 0.04
LOCAL_PERSONAL_LR = 0.08


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _difficulty(value: str) -> float:
    return {
        'none': 0.0,
        'no': 0.0,
        'light': 0.25,
        'mild': 0.25,
        'a_little': 0.25,
        'moderate': 0.5,
        'yes': 0.6,
        'high': 0.8,
        'very_high': 1.0,
        'strong': 1.0,
        'unknown': 0.2,
    }.get(value, 0.0)


def _light(value: str) -> float:
    return {'soft': 0.15, 'normal': 0.35, 'bright': 0.7, 'harsh': 1.0}.get(value, 0.35)


def _crowd(value: str) -> float:
    return {'none': 0.0, 'low': 0.25, 'medium': 0.55, 'high': 0.8, 'very_high': 1.0}.get(value, 0.25)


def _breathing(value: str) -> float:
    return {'normal': 0.0, 'slightly_fast': 0.35, 'fast': 0.7, 'difficult': 1.0}.get(value, 0.0)


def extract_features(payload: dict[str, Any]) -> list[float]:
    user_context = payload.get('user_context', {})
    environment = payload.get('environment', {})
    sensor_data = payload.get('sensor_data', {})
    mobility_context = payload.get('mobility_context', {})
    observable_signs = payload.get('observable_signs', {})

    heart_rate = sensor_data.get('heart_rate')
    heart_load = 0.0
    if isinstance(heart_rate, (int, float)):
        heart_load = _clamp((heart_rate - 70) / 55)

    return [
        _clamp((6 - float(user_context.get('energy_level', 3))) / 5),
        _breathing(user_context.get('breathing_state', 'normal')),
        _clamp(float(environment.get('noise_level', 1)) / 4),
        _light(environment.get('light_level', 'normal')),
        _crowd(environment.get('crowd_density', 'low')),
        max(
            _difficulty(environment.get('routine_disruption', 'none')),
            _difficulty(environment.get('transition_difficulty', 'none')),
            _difficulty(mobility_context.get('transport_difficulty', 'none')),
        ),
        max(
            heart_load,
            _clamp((6 - float(sensor_data.get('sleep_quality', 3))) / 5),
        ),
        max(
            _difficulty(user_context.get('need_isolation', 'no')),
            1.0 if observable_signs.get('shutdown_signs', False) else 0.0,
            0.7 if observable_signs.get('increased_stimming', False) else 0.0,
            0.6 if observable_signs.get('pacing_agitation', False) else 0.0,
        ),
        1.0,
    ]


async def _fetch_mec_shared_model() -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(f'{MEC_API_URL.rstrip("/")}/fl/model')
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


async def _fetch_cloud_regional_model() -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(
                f'{API_BASE_URL.rstrip("/")}/federated/regional-model',
                params={'region': MEC_REGION, 'mecNodeName': MEC_NODE_NAME},
            )
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


async def ensure_phone_model_initialized() -> dict[str, Any]:
    state = app.storage.user.get('personalized_fl')
    model = await _fetch_mec_shared_model()
    source = 'mec'
    if not model:
        model = await _fetch_cloud_regional_model()
        source = 'cloud'

    if not isinstance(state, dict):
        shared_weights = model.get('sharedWeights') if model else DEFAULT_SHARED_WEIGHTS
        state = {
            'region': model.get('region', MEC_REGION) if model else MEC_REGION,
            'mec_node': model.get('name', MEC_NODE_NAME) if model else MEC_NODE_NAME,
            'shared_version': model.get('version', 'local-default') if model else 'local-default',
            'shared_source': source if model else 'local-default',
            'shared_weights': [float(value) for value in shared_weights],
            'personal_weights': [0.0 for _ in shared_weights],
            'round': 0,
        }
        app.storage.user['personalized_fl'] = state
        return state

    if model and model.get('region') != state.get('region'):
        shared_weights = model.get('sharedWeights') or state['shared_weights']
        state['region'] = model.get('region', MEC_REGION)
        state['mec_node'] = model.get('name', MEC_NODE_NAME)
        state['shared_version'] = model.get('version', 'regional')
        state['shared_source'] = source
        state['shared_weights'] = [float(value) for value in shared_weights]
        # Preserve personal_weights vi exactly across region switches.
        app.storage.user['personalized_fl'] = state

    return state


def _prediction(score: float) -> dict[str, Any]:
    if score < 0.34:
        stress_level = 'calm'
        title = 'You seem calm right now'
        recommendation = 'You appear stable. This could be a good moment for a focused task.'
    elif score < 0.67:
        stress_level = 'alert'
        title = 'You may be under some pressure'
        recommendation = 'Try a short pause, reduce stimulation if possible, and check for a quieter space.'
    else:
        stress_level = 'high'
        title = 'Your stress seems elevated'
        recommendation = 'Move to a calm place if possible and begin a guided breathing or support routine.'

    return {
        'stress_level': stress_level,
        'score': round(score, 2),
        'confidence': round(_clamp(0.66 + score * 0.24, 0.66, 0.93), 2),
        'title': title,
        'recommendation': recommendation,
        'model': 'phone-personalized-fl-linear-v1',
    }


def _publish_shared_update(state: dict[str, Any], sample_count: int = 1) -> bool:
    try:
        import paho.mqtt.client as mqtt
    except Exception:
        return False

    user = get_current_user() or {}
    client_id = str(user.get('id') or user.get('email') or 'web-phone')
    payload = {
        'client_id': client_id,
        'region': state.get('region', MEC_REGION),
        'mec_node': state.get('mec_node', MEC_NODE_NAME),
        'shared_weights': state['shared_weights'],
        'n_samples': sample_count,
        'timestamp': time.time(),
        'personal_component_included': False,
    }

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, f'{client_id}-web')
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 5)
        client.publish('tsa/fl/update', payload=json.dumps(payload))
        client.disconnect()
        return True
    except Exception:
        return False


async def train_personalized_phone_model(payload: dict[str, Any]) -> dict[str, Any]:
    state = await ensure_phone_model_initialized()
    features = extract_features(payload)
    shared = state['shared_weights']
    personal = state['personal_weights']
    effective = [s + p for s, p in zip(shared, personal)]

    score = _sigmoid(sum(weight * value for weight, value in zip(effective, features)))
    target = 1.0 if score >= 0.55 or features[7] >= 0.7 else 0.0
    gradient_scale = score - target

    for index, feature in enumerate(features):
        gradient = gradient_scale * feature
        shared[index] -= LOCAL_SHARED_LR * gradient
        personal[index] -= LOCAL_PERSONAL_LR * gradient

    state['round'] = int(state.get('round', 0)) + 1
    state['shared_weights'] = [round(value, 8) for value in shared]
    state['personal_weights'] = [round(value, 8) for value in personal]
    app.storage.user['personalized_fl'] = state

    published = _publish_shared_update(state)
    prediction = _prediction(score)
    prediction['pfl'] = {
        'effective_model': 'wi = ws + vi',
        'shared_component': 'ws updated locally and sent to MEC',
        'personal_component': 'vi updated locally and kept on phone',
        'region': state.get('region'),
        'shared_version': state.get('shared_version'),
        'shared_source': state.get('shared_source'),
        'mqtt_update_sent': published,
    }
    return prediction
