import asyncio
from datetime import datetime, timezone

from nicegui import app, ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.guards.auth_guard import require_auth
from app.services.activity_service import add_activity_entry
from app.services.checkin_service import build_mock_prediction
from app.services.admin_analytics_service import register_admin_event
from app.theme import register_theme


@ui.page('/check-in')
def checkin_page() -> None:
    register_theme()
    if not require_auth():
        return

    ui.element('div').classes('nm-hero-blur')

    form = {
        'energy_level': 3,
        'breathing_state': 'normal',
        'physical_discomfort': 0,
        'speaking_difficulty': 'none',
        'need_isolation': 'no',
        'noise_level': 2,
        'light_level': 'normal',
        'crowd_density': 'low',
        'routine_disruption': 'none',
        'transition_difficulty': 'none',
        'social_load': 'low',
        'calm_space_available': 'yes',
        'heart_rate': None,
        'has_wearable': False,
        'hrv': None,
        'sleep_quality': 3,
        'transport_mode': 'walking',
        'transport_difficulty': 'none',
        'pacing_agitation': False,
        'increased_stimming': False,
        'shutdown_signs': False,
    }

    state = {'step': 1}

    def set_value(key: str, value):
        form[key] = value
        render_summary.refresh()
        render_step.refresh()

    def current_step_title() -> str:
        return {
            1: 'How are you feeling right now?',
            2: 'What is your environment like?',
            3: 'Optional sensor & context data',
        }[state['step']]

    def current_step_subtitle() -> str:
        return {
            1: 'Describe your current internal state.',
            2: 'Describe your sensory and social environment.',
            3: 'Add richer context if available.',
        }[state['step']]

    def progress_value() -> float:
        return state['step'] / 3

    def build_payload() -> dict:
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source': 'manual_checkin',
            'user_context': {
                'energy_level': form['energy_level'],
                'breathing_state': form['breathing_state'],
                'physical_discomfort': form['physical_discomfort'],
                'speaking_difficulty': form['speaking_difficulty'],
                'need_isolation': form['need_isolation'],
            },
            'environment': {
                'noise_level': form['noise_level'],
                'light_level': form['light_level'],
                'crowd_density': form['crowd_density'],
                'routine_disruption': form['routine_disruption'],
                'transition_difficulty': form['transition_difficulty'],
                'social_load': form['social_load'],
                'calm_space_available': form['calm_space_available'],
            },
            'sensor_data': {
                'heart_rate': form['heart_rate'],
                'has_wearable': form['has_wearable'],
                'hrv': form['hrv'] if form['has_wearable'] else None,
                'sleep_quality': form['sleep_quality'],
            },
            'mobility_context': {
                'transport_mode': form['transport_mode'],
                'transport_difficulty': form['transport_difficulty'],
            },
            'observable_signs': {
                'pacing_agitation': form['pacing_agitation'],
                'increased_stimming': form['increased_stimming'],
                'shutdown_signs': form['shutdown_signs'],
            },
        }

    def step_chip(step_number: int) -> tuple[str, str]:
        if step_number == state['step']:
            return f'Step {step_number}', 'nm-step-chip nm-step-chip-active'
        if step_number < state['step']:
            return f'Step {step_number}', 'nm-step-chip nm-step-chip-done'
        return f'Step {step_number}', 'nm-step-chip'

    def go_next():
        state['step'] = min(3, state['step'] + 1)
        render_header.refresh()
        render_step.refresh()
        render_summary.refresh()

    def go_back():
        state['step'] = max(1, state['step'] - 1)
        render_header.refresh()
        render_step.refresh()
        render_summary.refresh()

    async def submit():
        payload = build_payload()
        app.storage.user['last_checkin'] = payload

        loading_dialog = ui.dialog().props('persistent')
        with loading_dialog:
            with ui.card().classes('nm-surface-card p-6 min-w-[300px] items-center'):
                ui.spinner('dots', size='lg', color='primary')
                ui.label('Analyzing your check-in...').classes('text-lg font-semibold mt-3')
                ui.label('Generating a mock stress estimate').classes('nm-small')

        loading_dialog.open()
        await asyncio.sleep(1.2)

        prediction = build_mock_prediction(payload)
        app.storage.user['last_prediction'] = prediction
        # user-scoped activity history (UI/session cache)
        add_activity_entry(payload, prediction)
        # shared admin analytics cache (simulates backend/external DB aggregation)
        register_admin_event(payload, prediction)

        loading_dialog.close()
        ui.notify('Check-in analyzed successfully', color='positive')
        ui.navigate.to('/')

    def section_title(title: str, subtitle: str | None = None):
        ui.label(title).classes('nm-field-title')
        if subtitle:
            ui.label(subtitle).classes('nm-field-subtitle')

    def slider_card(title: str, key: str, min_value: int, max_value: int, subtitle: str | None = None):
        with ui.card().classes('nm-field-card w-full'):
            with ui.row().classes('w-full items-start justify-between gap-3'):
                with ui.column().classes('gap-0'):
                    section_title(title, subtitle)
                value_badge = ui.label(str(form[key])).classes('nm-value-pill')

            def on_change(e, k=key):
                set_value(k, e.value)
                value_badge.set_text(str(e.value))

            ui.slider(
                min=min_value,
                max=max_value,
                value=form[key],
                step=1,
                on_change=on_change,
            ).classes('w-full mt-5')

            with ui.row().classes('w-full justify-between mt-2 text-[0.78rem] text-[#8A92A3]'):
                ui.label(str(min_value))
                ui.label(str(max_value))

    def choice_card(title: str, key: str, options: dict, subtitle: str | None = None):
        with ui.card().classes('nm-field-card w-full'):
            section_title(title, subtitle)
            ui.toggle(
                options,
                value=form[key],
                on_change=lambda e, k=key: set_value(k, e.value),
            ).props('unelevated no-caps spread').classes('w-full mt-4')

    def number_card(title: str, key: str, placeholder: str, suffix: str = '', subtitle: str | None = None):
        with ui.card().classes('nm-field-card w-full'):
            section_title(title, subtitle)
            ui.number(
                label=title,
                value=form[key],
                placeholder=placeholder,
                on_change=lambda e, k=key: set_value(k, e.value),
            ).props(f'outlined suffix="{suffix}"').classes('w-full mt-4')

    @ui.refreshable
    def render_header():
        with ui.column().classes('w-full gap-4 mb-6'):
            with ui.card().classes('nm-form-hero w-full'):
                with ui.row().classes('w-full items-start justify-between gap-4 flex-wrap'):
                    with ui.column().classes('gap-1'):
                        ui.label('NeuroMove Check-in').classes('text-sm uppercase tracking-[0.18em] text-[#6E7687]')
                        ui.label(current_step_title()).classes('nm-page-title text-left')
                        ui.label(current_step_subtitle()).classes('nm-subtitle text-[1.02rem]')

                    with ui.row().classes('items-center gap-2'):
                        with ui.row().classes('nm-mini-badge'):
                            ui.icon('shield')
                            ui.label('Privacy-first')
                        with ui.row().classes('nm-mini-badge'):
                            ui.icon('memory')
                            ui.label('Backend-ready')

                ui.linear_progress(value=progress_value()).props('rounded color=primary').classes('w-full mt-4')

                with ui.row().classes('w-full gap-2 flex-wrap mt-4'):
                    for i in [1, 2, 3]:
                        text, classes = step_chip(i)
                        ui.label(text).classes(classes)

    @ui.refreshable
    def render_summary():
        payload = build_payload()

        with ui.card().classes('nm-summary-card w-full lg:sticky lg:top-8'):
            ui.label('Live summary').classes('text-xl font-bold text-[#0B4A38]')
            ui.label('Preview of the information that will be sent to the backend later.').classes('nm-small mb-4')

            with ui.column().classes('gap-4'):
                with ui.element('div').classes('nm-summary-block'):
                    ui.label('Current state').classes('font-semibold text-[#0B4A38]')
                    with ui.row().classes('gap-2 mt-3 flex-wrap'):
                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Energy').classes('nm-kpi-label')
                            ui.label(str(payload['user_context']['energy_level'])).classes('nm-kpi-value')

                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Breathing').classes('nm-kpi-label')
                            ui.label(payload['user_context']['breathing_state']).classes('nm-kpi-value')

                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Isolation').classes('nm-kpi-label')
                            ui.label(payload['user_context']['need_isolation']).classes('nm-kpi-value')

                with ui.element('div').classes('nm-summary-block'):
                    ui.label('Environment').classes('font-semibold text-[#0B4A38]')
                    ui.label(
                        f"Noise {payload['environment']['noise_level']} · "
                        f"Light {payload['environment']['light_level']} · "
                        f"Crowd {payload['environment']['crowd_density']}"
                    ).classes('nm-small mt-2')

                with ui.element('div').classes('nm-summary-block'):
                    ui.label('Optional context').classes('font-semibold text-[#0B4A38]')
                    ui.label(
                        f"Heart rate: {payload['sensor_data']['heart_rate'] or '—'} · "
                        f"HRV: {payload['sensor_data']['hrv'] or '—'} · "
                        f"Sleep: {payload['sensor_data']['sleep_quality']}"
                    ).classes('nm-small mt-2')

            with ui.expansion('Payload preview').classes('w-full mt-5'):
                ui.code(str(payload)).classes('w-full text-xs')

    @ui.refreshable
    def render_step():
        with ui.column().classes('w-full gap-5'):
            if state['step'] == 1:
                with ui.element('div').classes('nm-section-grid'):
                    slider_card('Energy level', 'energy_level', 1, 5, '1 = very low, 5 = high')
                    choice_card(
                        'Breathing',
                        'breathing_state',
                        {
                            'normal': 'Normal',
                            'slightly_fast': 'Slightly fast',
                            'fast': 'Fast',
                            'difficult': 'Difficult',
                        },
                    )
                    slider_card(
                        'Physical discomfort',
                        'physical_discomfort',
                        0,
                        4,
                        'Pain, hunger, thirst, bathroom need, or body discomfort',
                    )
                    choice_card(
                        'Difficulty speaking',
                        'speaking_difficulty',
                        {
                            'none': 'None',
                            'mild': 'Mild',
                            'moderate': 'Moderate',
                            'high': 'High',
                        },
                    )
                    choice_card(
                        'Need to isolate',
                        'need_isolation',
                        {
                            'no': 'No',
                            'a_little': 'A little',
                            'yes': 'Yes',
                            'strong': 'Strong',
                        },
                    )

            elif state['step'] == 2:
                with ui.element('div').classes('nm-section-grid'):
                    slider_card('Noise', 'noise_level', 1, 4, '1 = calm, 4 = very loud')
                    choice_card(
                        'Light',
                        'light_level',
                        {
                            'soft': 'Soft',
                            'normal': 'Normal',
                            'bright': 'Bright',
                            'harsh': 'Harsh',
                        },
                    )
                    choice_card(
                        'Crowd',
                        'crowd_density',
                        {
                            'none': 'None',
                            'low': 'Low',
                            'medium': 'Medium',
                            'high': 'High',
                            'very_high': 'Very high',
                        },
                    )
                    choice_card(
                        'Unexpected change / routine disruption',
                        'routine_disruption',
                        {
                            'none': 'None',
                            'light': 'Light',
                            'moderate': 'Moderate',
                            'high': 'High',
                        },
                    )
                    choice_card(
                        'Transition / waiting difficulty',
                        'transition_difficulty',
                        {
                            'none': 'None',
                            'light': 'Light',
                            'moderate': 'Moderate',
                            'high': 'High',
                        },
                    )
                    choice_card(
                        'Social / communication demand',
                        'social_load',
                        {
                            'low': 'Low',
                            'moderate': 'Moderate',
                            'high': 'High',
                            'very_high': 'Very high',
                        },
                    )
                    choice_card(
                        'Quiet space available',
                        'calm_space_available',
                        {
                            'yes': 'Yes',
                            'no': 'No',
                            'unknown': 'Unknown',
                        },
                    )

            elif state['step'] == 3:
                with ui.element('div').classes('nm-section-grid'):
                    number_card('Heart rate', 'heart_rate', 'e.g. 92', 'bpm')

                    with ui.card().classes('nm-field-card w-full'):
                        section_title('Connected wearable', 'Enable if HRV data is available')
                        wearable_switch = ui.switch(
                            'Wearable available',
                            value=form['has_wearable'],
                            on_change=lambda e: set_value('has_wearable', e.value),
                        ).props('color=primary').classes('mt-4')

                        with ui.column().classes('w-full mt-4').bind_visibility_from(wearable_switch, 'value'):
                            ui.number(
                                label='Heart rate variability',
                                value=form['hrv'],
                                placeholder='e.g. 31',
                                on_change=lambda e: set_value('hrv', e.value),
                            ).props('outlined suffix="ms"').classes('w-full')

                    slider_card(
                        'Sleep quality (last night)',
                        'sleep_quality',
                        1,
                        5,
                        '1 = very poor, 5 = very good',
                    )

                    with ui.card().classes('nm-field-card w-full'):
                        section_title('Transport mode')
                        ui.select(
                            ['walking', 'bus', 'metro', 'car', 'train', 'other'],
                            value=form['transport_mode'],
                            on_change=lambda e: set_value('transport_mode', e.value),
                            label='Transport mode',
                        ).props('outlined').classes('w-full mt-4')

                    choice_card(
                        'Transport / movement difficulty',
                        'transport_difficulty',
                        {
                            'none': 'None',
                            'light': 'Light',
                            'moderate': 'Moderate',
                            'high': 'High',
                        },
                    )

                    with ui.card().classes('nm-field-card w-full'):
                        section_title('Observable signs')
                        with ui.column().classes('w-full gap-3 mt-4'):
                            ui.switch(
                                'Agitation / pacing',
                                value=form['pacing_agitation'],
                                on_change=lambda e: set_value('pacing_agitation', e.value),
                            ).props('color=primary')
                            ui.switch(
                                'More stimming than usual',
                                value=form['increased_stimming'],
                                on_change=lambda e: set_value('increased_stimming', e.value),
                            ).props('color=primary')
                            ui.switch(
                                'Sudden freezing / shutdown signs',
                                value=form['shutdown_signs'],
                                on_change=lambda e: set_value('shutdown_signs', e.value),
                            ).props('color=primary')

            with ui.element('div').classes('nm-action-row'):
                with ui.card().classes('nm-surface-card w-full p-3 mt-2'):
                    with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                        ui.button(
                            'Back',
                            on_click=go_back,
                        ).props('outline no-caps').classes('min-w-[120px]').set_visibility(state['step'] > 1)

                        with ui.row().classes('items-center gap-3 ml-auto'):
                            if state['step'] < 3:
                                ui.button(
                                    'Next',
                                    on_click=go_next,
                                ).props('unelevated no-caps icon=arrow_forward').classes('min-w-[150px] nm-primary-btn')
                            else:
                                ui.button(
                                    'Submit check-in',
                                    on_click=submit,
                                ).props('unelevated no-caps icon=check_circle').classes('min-w-[190px] nm-primary-btn')

    with screen_container():
        app_shell(active='', show_device_badge=True)

        with ui.element('div').classes('w-full max-w-[1200px] mx-auto'):
            render_header()

            with ui.element('div').classes('grid grid-cols-1 lg:grid-cols-[1.12fr_0.88fr] gap-8 items-start'):
                render_step()
                render_summary()

        ui.element('div').classes('h-24')
        bottom_nav('')