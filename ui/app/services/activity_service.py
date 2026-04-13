from __future__ import annotations

from datetime import datetime
from typing import Any

from nicegui import app


CACHE_KEY = 'checkin_history_cache'


def _safe_get_history() -> list[dict[str, Any]]:
    history = app.storage.user.get(CACHE_KEY, [])
    if not isinstance(history, list):
        return []
    return history


def _format_title(payload: dict[str, Any], prediction: dict[str, Any]) -> str:
    level = prediction.get('stress_level', 'calm')

    if level == 'high':
        return 'High stress check-in'
    if level == 'alert':
        return 'Elevated stress check-in'
    return 'Calm state check-in'


def _format_context_label(payload: dict[str, Any]) -> str:
    transport_mode = payload.get('mobility_context', {}).get('transport_mode')
    social_load = payload.get('environment', {}).get('social_load')

    parts = []

    if transport_mode and transport_mode != 'walking':
        parts.append(transport_mode.replace('_', ' ').title())

    if social_load in ('high', 'very_high'):
        parts.append('social demand')

    if not parts:
        return 'Daily check-in'

    return ' · '.join(parts)


def build_activity_entry(payload: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    timestamp = payload.get('timestamp')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_label = dt.strftime('%H:%M')
            date_label = dt.strftime('%Y-%m-%d')
        except Exception:
            time_label = '--:--'
            date_label = ''
    else:
        time_label = '--:--'
        date_label = ''

    level = prediction.get('stress_level', 'calm')

    icon_map = {
        'calm': 'spa',
        'alert': 'visibility',
        'high': 'priority_high',
    }

    return {
        'timestamp': timestamp,
        'date': date_label,
        'time': time_label,
        'title': _format_title(payload, prediction),
        'subtitle': _format_context_label(payload),
        'level': level,
        'icon': icon_map.get(level, 'spa'),
        'score': prediction.get('score'),
        'confidence': prediction.get('confidence'),
        'recommendation': prediction.get('recommendation'),
        'payload': payload,
        'prediction': prediction,
    }


def add_activity_entry(payload: dict[str, Any], prediction: dict[str, Any]) -> None:
    """
    Temporary UI cache only.
    Final source of truth will be the backend + external database.
    """
    history = _safe_get_history()
    entry = build_activity_entry(payload, prediction)
    history.insert(0, entry)
    app.storage.user[CACHE_KEY] = history[:20]  # keep only latest 20 locally


def get_activity_history() -> list[dict[str, Any]]:
    """
    Frontend access point for activity history.
    Today: local session cache.
    Future: replace with backend API fetch.
    """
    return _safe_get_history()


def get_latest_activity_entry() -> dict[str, Any] | None:
    history = _safe_get_history()
    return history[0] if history else None


def clear_activity_history_cache() -> None:
    app.storage.user.pop(CACHE_KEY, None)