def current_state() -> dict:
    return {'label': 'Stability', 'title': 'You seem calm right now',
            'description': 'Your neurological patterns are steady. This is a great time for a focused task.',
            'level': 'calm', 'device_mode': 'On Device'}

def settings_state() -> dict:
    return {'vibration_only': True, 'sound_alerts': False, 'federated_learning': True,
            'contacts': [{'name': 'Sarah Chen', 'image': 'https://picsum.photos/seed/sarah/80/80'},
                         {'name': 'Marcus Miller', 'image': 'https://picsum.photos/seed/marcus/80/80'}],
            'version': '1.2.0'}
