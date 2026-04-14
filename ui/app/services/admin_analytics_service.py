from __future__ import annotations

import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from nicegui import app

from app.core.config import USE_MOCK_ADMIN_ANALYTICS

ADMIN_EVENTS_KEY = 'admin_analytics_events'

DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
HOUR_BUCKETS = [6, 8, 10, 12, 14, 16, 18, 20]


def _safe_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except Exception:
        return datetime.now(timezone.utc)


def _stress_band(score: float) -> str:
    if score < 0.34:
        return 'calm'
    if score < 0.67:
        return 'alert'
    return 'high'


def _bucket_hour(hour: int) -> int:
    for bucket in reversed(HOUR_BUCKETS):
        if hour >= bucket:
            return bucket
    return HOUR_BUCKETS[0]


def _light_score(value: str) -> int:
    return {
        'soft': 1,
        'normal': 2,
        'bright': 3,
        'harsh': 4,
    }.get(value, 2)


def _crowd_score(value: str) -> int:
    return {
        'none': 0,
        'low': 1,
        'medium': 2,
        'high': 3,
        'very_high': 4,
    }.get(value, 1)


def _difficulty_score(value: str) -> int:
    return {
        'none': 0,
        'no': 0,
        'light': 1,
        'mild': 1,
        'a_little': 1,
        'moderate': 2,
        'yes': 2,
        'high': 3,
        'very_high': 4,
        'strong': 4,
        'unknown': 1,
    }.get(value, 0)


def _breathing_score(value: str) -> int:
    return {
        'normal': 0,
        'slightly_fast': 1,
        'fast': 2,
        'difficult': 4,
    }.get(value, 0)


def _support_flag_from_event(event: dict[str, Any]) -> bool:
    return (
        event['stress_level'] == 'high'
        or event['need_isolation'] >= 2
        or event['calm_space_available'] == 0
        or event['shutdown_signs'] == 1
    )


def _transport_score(mode: str, difficulty: str) -> int:
    base = _difficulty_score(difficulty)
    if mode in ('metro', 'train', 'bus'):
        base += 1
    return base


def _build_event_from_payload(payload: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    user_context = payload.get('user_context', {})
    environment = payload.get('environment', {})
    sensor_data = payload.get('sensor_data', {})
    mobility_context = payload.get('mobility_context', {})
    observable_signs = payload.get('observable_signs', {})

    dt = _safe_datetime(payload.get('timestamp'))

    event = {
        'timestamp': dt.isoformat(),
        'day_label': DAY_LABELS[dt.weekday()],
        'hour_bucket': _bucket_hour(dt.hour),
        'stress_score': float(prediction.get('score', 0.0)),
        'stress_level': prediction.get('stress_level', 'calm'),

        # internal / physiological
        'energy_level': int(user_context.get('energy_level', 3)),
        'breathing_state': _breathing_score(user_context.get('breathing_state', 'normal')),
        'physical_discomfort': int(user_context.get('physical_discomfort', 0)),
        'speaking_difficulty': _difficulty_score(user_context.get('speaking_difficulty', 'none')),
        'need_isolation': _difficulty_score(user_context.get('need_isolation', 'no')),

        # environment
        'noise_level': int(environment.get('noise_level', 1)),
        'light_level': _light_score(environment.get('light_level', 'normal')),
        'crowd_density': _crowd_score(environment.get('crowd_density', 'low')),
        'routine_disruption': _difficulty_score(environment.get('routine_disruption', 'none')),
        'transition_difficulty': _difficulty_score(environment.get('transition_difficulty', 'none')),
        'social_load': _difficulty_score(environment.get('social_load', 'low')),
        'calm_space_available': 1 if environment.get('calm_space_available', 'yes') == 'yes' else 0,

        # sensors
        'heart_rate': sensor_data.get('heart_rate'),
        'has_wearable': bool(sensor_data.get('has_wearable', False)),
        'hrv': sensor_data.get('hrv'),
        'sleep_quality': int(sensor_data.get('sleep_quality', 3)),

        # mobility
        'transport_mode': mobility_context.get('transport_mode', 'walking'),
        'transport_difficulty': _difficulty_score(mobility_context.get('transport_difficulty', 'none')),

        # observable signs
        'pacing_agitation': 1 if observable_signs.get('pacing_agitation', False) else 0,
        'increased_stimming': 1 if observable_signs.get('increased_stimming', False) else 0,
        'shutdown_signs': 1 if observable_signs.get('shutdown_signs', False) else 0,

        # text fields
        'recommendation': prediction.get('recommendation', ''),
        'prediction_title': prediction.get('title', ''),
    }

    event['support_flag'] = 1 if _support_flag_from_event(event) else 0
    return event


def register_admin_event(payload: dict[str, Any], prediction: dict[str, Any]) -> None:
    """
    Shared temporary analytics cache.
    This simulates what the backend/external DB aggregation layer will provide later.
    """
    event = _build_event_from_payload(payload, prediction)
    events = app.storage.general.get(ADMIN_EVENTS_KEY, [])
    if not isinstance(events, list):
        events = []
    events.append(event)
    app.storage.general[ADMIN_EVENTS_KEY] = events[-1000:]


def _seed_mock_events_if_needed() -> list[dict[str, Any]]:
    events = app.storage.general.get(ADMIN_EVENTS_KEY, [])
    if isinstance(events, list) and len(events) > 0:
        return events

    if not USE_MOCK_ADMIN_ANALYTICS:
        return []

    rng = random.Random(42)
    seeded: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for day_offset in range(6, -1, -1):
        for _ in range(rng.randint(4, 8)):
            hour_bucket = rng.choice(HOUR_BUCKETS)
            dt = (now - timedelta(days=day_offset)).replace(
                hour=hour_bucket,
                minute=rng.choice([0, 15, 30, 45]),
                second=0,
                microsecond=0,
            )

            weekday_boost = 0.08 if dt.weekday() in (2, 3, 4) else 0.0
            midday_boost = 0.12 if hour_bucket in (12, 14, 16) else 0.0
            base_score = min(0.85, max(0.15, rng.uniform(0.18, 0.68) + weekday_boost + midday_boost))

            stress_level = _stress_band(base_score)

            event = {
                'timestamp': dt.isoformat(),
                'day_label': DAY_LABELS[dt.weekday()],
                'hour_bucket': hour_bucket,
                'stress_score': round(base_score, 2),
                'stress_level': stress_level,

                'energy_level': rng.randint(1, 5),
                'breathing_state': rng.choice([0, 1, 2, 4]),
                'physical_discomfort': rng.randint(0, 4),
                'speaking_difficulty': rng.randint(0, 4),
                'need_isolation': rng.randint(0, 4),

                'noise_level': rng.randint(1, 4),
                'light_level': rng.randint(1, 4),
                'crowd_density': rng.randint(0, 4),
                'routine_disruption': rng.randint(0, 4),
                'transition_difficulty': rng.randint(0, 4),
                'social_load': rng.randint(0, 4),
                'calm_space_available': rng.choice([0, 1]),

                'heart_rate': rng.choice([None, rng.randint(72, 118)]),
                'has_wearable': rng.choice([True, False]),
                'hrv': rng.choice([None, rng.randint(18, 62)]),
                'sleep_quality': rng.randint(1, 5),

                'transport_mode': rng.choice(['walking', 'bus', 'metro', 'car', 'train']),
                'transport_difficulty': rng.randint(0, 4),

                'pacing_agitation': rng.choice([0, 1]),
                'increased_stimming': rng.choice([0, 1]),
                'shutdown_signs': 1 if stress_level == 'high' and rng.random() > 0.6 else 0,

                'recommendation': rng.choice([
                    'Move to a quieter place and take a short pause.',
                    'Try a 2-minute breathing routine.',
                    'Reduce sensory input and check for a calm space.',
                    'Consider contacting a trusted person if needed.',
                ]),
                'prediction_title': 'Mock analytics seed',
            }
            event['support_flag'] = 1 if _support_flag_from_event(event) else 0
            seeded.append(event)

    app.storage.general[ADMIN_EVENTS_KEY] = seeded
    return seeded


def _get_events() -> list[dict[str, Any]]:
    events = _seed_mock_events_if_needed()
    return events if isinstance(events, list) else []


def _compute_overview(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {
            'active_sessions': 0,
            'avg_stress_score': 0.0,
            'support_flags': 0,
            'last_update': None,
        }

    return {
        'active_sessions': max(1, round(len(events) / 3)),
        'avg_stress_score': round(mean(e['stress_score'] for e in events), 2),
        'support_flags': sum(e['support_flag'] for e in events),
        'last_update': max(e['timestamp'] for e in events),
    }


def _compute_daily_trend(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for event in events:
        grouped[event['day_label']].append(event['stress_score'])

    result = []
    for day in DAY_LABELS:
        scores = grouped.get(day, [])
        result.append({
            'day': day,
            'score': round(mean(scores), 2) if scores else 0.0,
        })
    return result


def _compute_heatmap(events: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)

    for event in events:
        day_index = DAY_LABELS.index(event['day_label'])
        hour_index = HOUR_BUCKETS.index(event['hour_bucket'])
        grouped[(hour_index, day_index)].append(event['stress_score'])

    values = []
    for day_index in range(len(DAY_LABELS)):
        for hour_index in range(len(HOUR_BUCKETS)):
            scores = grouped.get((hour_index, day_index), [])
            scaled = int(round(mean(scores) * 5)) if scores else 0
            values.append([hour_index, day_index, min(5, scaled)])

    return {
        'hours': [str(h).zfill(2) for h in HOUR_BUCKETS],
        'days': DAY_LABELS,
        'values': values,
    }


def _compute_trigger_distribution(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weights = Counter()

    for event in events:
        weights['Noise'] += event['noise_level'] * 1.6
        weights['Light'] += event['light_level'] * 1.0
        weights['Crowd'] += event['crowd_density'] * 1.5
        weights['Routine'] += event['routine_disruption'] * 1.4
        weights['Transitions'] += event['transition_difficulty'] * 1.3
        weights['Social / Communication'] += (event['social_load'] + event['speaking_difficulty']) * 1.2
        weights['Transit'] += _transport_score(event['transport_mode'], str(event['transport_difficulty'])) * 1.15

        if event['calm_space_available'] == 0:
            weights['Quiet-space absence'] += 3.0

        fatigue_load = (6 - event['energy_level']) + (6 - event['sleep_quality'])
        weights['Fatigue / Sleep'] += fatigue_load * 0.9

        physiological_load = (
            event['breathing_state'] +
            event['physical_discomfort'] +
            (2 if isinstance(event['heart_rate'], (int, float)) and event['heart_rate'] >= 95 else 0) +
            (2 if isinstance(event['hrv'], (int, float)) and event['hrv'] < 35 else 0)
        )
        weights['Physiological load'] += physiological_load * 0.9

        behavior_load = (
            event['pacing_agitation'] +
            event['increased_stimming'] +
            (2 * event['shutdown_signs']) +
            event['need_isolation']
        )
        weights['Behavioral strain'] += behavior_load * 1.1

    ordered = weights.most_common(8)
    return [{'label': label, 'value': round(value)} for label, value in ordered]


def _compute_radar_profile(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {'values': [0, 0, 0, 0, 0, 0]}

    def avg(key: str) -> float:
        return mean(e[key] for e in events)

    values = [
        round(avg('noise_level') / 4 * 100),
        round(avg('light_level') / 4 * 100),
        round(avg('crowd_density') / 4 * 100),
        round(avg('routine_disruption') / 4 * 100),
        round((avg('social_load') + avg('speaking_difficulty')) / 8 * 100),
        round(mean(_transport_score(e['transport_mode'], str(e['transport_difficulty'])) for e in events) / 5 * 100),
    ]
    return {'values': values}


def _compute_recommendation_distribution(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter = Counter()

    for event in events:
        if event['calm_space_available'] == 0 or event['noise_level'] >= 3 or event['crowd_density'] >= 3:
            counter['Quiet place'] += 1
        if event['breathing_state'] >= 2 or event['stress_level'] == 'high':
            counter['Breathing'] += 1
        if event['energy_level'] <= 2 or event['transition_difficulty'] >= 2:
            counter['Short pause'] += 1
        if event['shutdown_signs'] == 1 or event['social_load'] >= 3:
            counter['Trusted contact'] += 1

    if not counter:
        counter.update({
            'Quiet place': 1,
            'Breathing': 1,
            'Short pause': 1,
            'Trusted contact': 1,
        })

    return [{'label': k, 'value': v} for k, v in counter.items()]


def _compute_recent_alerts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flagged = [e for e in events if e['support_flag'] == 1]
    flagged.sort(key=lambda e: e['timestamp'], reverse=True)

    recent = []
    for event in flagged[:5]:
        dt = _safe_datetime(event['timestamp'])
        recent.append({
            'time': dt.strftime('%d/%m %H:%M'),
            'level': event['stress_level'],
            'title': 'Support flag raised',
            'details': (
                f"Noise {event['noise_level']} · Crowd {event['crowd_density']} · "
                f"Isolation {event['need_isolation']} · Social {event['social_load']}"
            ),
        })
    return recent


def _compute_cohort_cards(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {
            'physiological_burden': 0,
            'sensory_load': 0,
            'communication_friction': 0,
            'quiet_space_availability': 0,
        }

    physiological_burden = mean(
        (
            e['breathing_state']
            + e['physical_discomfort']
            + (1 if isinstance(e['heart_rate'], (int, float)) and e['heart_rate'] >= 95 else 0)
            + (1 if isinstance(e['hrv'], (int, float)) and e['hrv'] < 35 else 0)
        )
        for e in events
    )

    sensory_load = mean(
        e['noise_level'] + e['light_level'] + e['crowd_density']
        for e in events
    )

    communication_friction = mean(
        e['social_load'] + e['speaking_difficulty']
        for e in events
    )

    quiet_space_availability = round(mean(e['calm_space_available'] for e in events) * 100)

    return {
        'physiological_burden': round(physiological_burden, 2),
        'sensory_load': round(sensory_load, 2),
        'communication_friction': round(communication_friction, 2),
        'quiet_space_availability': quiet_space_availability,
    }


def _compute_federated_status(events: list[dict[str, Any]]) -> dict[str, Any]:
    overview = _compute_overview(events)
    avg_score = overview['avg_stress_score']
    support_flags = overview['support_flags']

    base = [96, 92, 97, 89, 94]
    penalties = [
        int(avg_score * 6),
        int(avg_score * 8),
        int(avg_score * 5),
        int(avg_score * 10) + (support_flags // 3),
        int(avg_score * 7),
    ]
    values = [max(70, b - p) for b, p in zip(base, penalties)]

    nodes = [
        {'name': 'Node A', 'health': values[0], 'status': 'online' if values[0] >= 85 else 'degraded'},
        {'name': 'Node B', 'health': values[1], 'status': 'online' if values[1] >= 85 else 'degraded'},
        {'name': 'Node C', 'health': values[2], 'status': 'online' if values[2] >= 85 else 'degraded'},
        {'name': 'Node D', 'health': values[3], 'status': 'online' if values[3] >= 85 else 'degraded'},
        {'name': 'Node E', 'health': values[4], 'status': 'online' if values[4] >= 85 else 'degraded'},
    ]

    return {
        'fl_round': 12 + min(8, support_flags),
        'global_model_version': 'v0.9.4-mock',
        'nodes': nodes,
    }


class MockAdminAnalyticsService:
    def get_dashboard_data(self) -> dict[str, Any]:
        events = _get_events()
        overview = _compute_overview(events)
        daily_trend = _compute_daily_trend(events)
        heatmap = _compute_heatmap(events)
        triggers = _compute_trigger_distribution(events)
        radar = _compute_radar_profile(events)
        recommendations = _compute_recommendation_distribution(events)
        recent_alerts = _compute_recent_alerts(events)
        cohort_cards = _compute_cohort_cards(events)
        federated_status = _compute_federated_status(events)

        return {
            'overview': overview,
            'trends': {
                'daily_trend': daily_trend,
                'heatmap': heatmap,
            },
            'triggers': triggers,
            'cohort_profile': radar,
            'cohort_cards': cohort_cards,
            'recommendations': recommendations,
            'recent_alerts': recent_alerts,
            'federated_status': federated_status,
            'events_count': len(events),
        }


class BackendAdminAnalyticsService:
    def get_dashboard_data(self) -> dict[str, Any]:
        raise NotImplementedError(
            'BackendAdminAnalyticsService is not implemented yet. '
            'Replace this with backend API calls when the backend/MEC layer is ready.'
        )


analytics_service = (
    MockAdminAnalyticsService()
    if USE_MOCK_ADMIN_ANALYTICS
    else BackendAdminAnalyticsService()
)