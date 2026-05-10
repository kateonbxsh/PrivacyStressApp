from __future__ import annotations

from typing import Any


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _energy_score(value: int) -> float:
    mapping = {
        1: 0.28,
        2: 0.20,
        3: 0.10,
        4: 0.03,
        5: 0.00,
    }
    return mapping.get(value, 0.10)


def _breathing_score(value: str) -> float:
    mapping = {
        'normal': 0.00,
        'slightly_fast': 0.10,
        'fast': 0.18,
        'difficult': 0.28,
    }
    return mapping.get(value, 0.00)


def _difficulty_score(value: str) -> float:
    mapping = {
        'none': 0.00,
        'light': 0.08,
        'mild': 0.08,
        'moderate': 0.16,
        'high': 0.26,
        'very_high': 0.30,
        'a_little': 0.08,
        'yes': 0.18,
        'strong': 0.28,
        'no': 0.00,
        'unknown': 0.05,
    }
    return mapping.get(value, 0.00)


def _binary_score(value: bool, weight: float) -> float:
    return weight if value else 0.0


def build_mock_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    user_context = payload.get('user_context', {})
    environment = payload.get('environment', {})
    sensor_data = payload.get('sensor_data', {})
    mobility_context = payload.get('mobility_context', {})
    observable_signs = payload.get('observable_signs', {})

    score = 0.10

    # --- user context ---
    score += _energy_score(user_context.get('energy_level', 3))
    score += _breathing_score(user_context.get('breathing_state', 'normal'))
    score += float(user_context.get('physical_discomfort', 0)) * 0.05
    score += _difficulty_score(user_context.get('speaking_difficulty', 'none'))
    score += _difficulty_score(user_context.get('need_isolation', 'no'))

    # --- environment ---
    score += max(0, int(environment.get('noise_level', 1)) - 1) * 0.05

    light_level = environment.get('light_level', 'normal')
    if light_level == 'bright':
        score += 0.07
    elif light_level == 'harsh':
        score += 0.12

    crowd_density = environment.get('crowd_density', 'low')
    crowd_map = {
        'none': 0.00,
        'low': 0.03,
        'medium': 0.08,
        'high': 0.16,
        'very_high': 0.22,
    }
    score += crowd_map.get(crowd_density, 0.00)

    score += _difficulty_score(environment.get('routine_disruption', 'none'))
    score += _difficulty_score(environment.get('transition_difficulty', 'none'))

    social_load = environment.get('social_load', 'low')
    social_map = {
        'low': 0.00,
        'moderate': 0.08,
        'high': 0.16,
        'very_high': 0.24,
    }
    score += social_map.get(social_load, 0.00)

    calm_space = environment.get('calm_space_available', 'yes')
    if calm_space == 'no':
        score += 0.14
    elif calm_space == 'unknown':
        score += 0.05

    # --- sensors ---
    heart_rate = sensor_data.get('heart_rate')
    if isinstance(heart_rate, (int, float)):
        if heart_rate >= 110:
            score += 0.18
        elif heart_rate >= 95:
            score += 0.10
        elif heart_rate >= 85:
            score += 0.05

    hrv = sensor_data.get('hrv')
    if isinstance(hrv, (int, float)):
        if hrv < 20:
            score += 0.18
        elif hrv < 35:
            score += 0.10
        elif hrv < 50:
            score += 0.04

    sleep_quality = sensor_data.get('sleep_quality', 3)
    if sleep_quality == 1:
        score += 0.18
    elif sleep_quality == 2:
        score += 0.10
    elif sleep_quality == 3:
        score += 0.03

    # --- mobility ---
    score += _difficulty_score(mobility_context.get('transport_difficulty', 'none'))

    # --- observable signs ---
    score += _binary_score(observable_signs.get('pacing_agitation', False), 0.10)
    score += _binary_score(observable_signs.get('increased_stimming', False), 0.12)
    score += _binary_score(observable_signs.get('shutdown_signs', False), 0.24)

    score = clamp(score)

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

    confidence = clamp(0.62 + score * 0.28, 0.62, 0.92)

    return {
        'stress_level': stress_level,
        'score': round(score, 2),
        'confidence': round(confidence, 2),
        'title': title,
        'recommendation': recommendation,
    }


def map_prediction_to_home_state(prediction: dict[str, Any]) -> dict[str, str]:
    level = prediction.get('stress_level', 'calm')

    if level == 'high':
        return {
            'label': 'Support',
            'title': prediction.get('title', 'Your stress seems elevated'),
            'description': prediction.get(
                'recommendation',
                'Move to a calm place if possible and begin a guided breathing or support routine.',
            ),
            'level': 'high',
            'device_mode': 'On Device',
        }

    if level == 'alert':
        return {
            'label': 'Attention',
            'title': prediction.get('title', 'You may be under some pressure'),
            'description': prediction.get(
                'recommendation',
                'Try a short pause, reduce stimulation if possible, and check for a quieter space.',
            ),
            'level': 'alert',
            'device_mode': 'On Device',
        }

    return {
        'label': 'Stability',
        'title': prediction.get('title', 'You seem calm right now'),
        'description': prediction.get(
            'recommendation',
            'You appear stable. This could be a good moment for a focused task.',
        ),
        'level': 'calm',
        'device_mode': 'On Device',
    }
