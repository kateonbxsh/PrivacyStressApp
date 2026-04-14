from nicegui import ui

from app.core.roles import USER_ROLE
from app.core.session import (
    get_current_role,
    get_onboarding_profile,
    has_completed_onboarding,
    is_auth,
    set_onboarding_completed,
    set_onboarding_profile,
)
from app.theme import register_theme


@ui.page('/onboarding')
def onboarding_page() -> None:
    register_theme()

    if not is_auth():
        ui.navigate.to('/login')
        return

    current_role = get_current_role()

    # researchers/admins do not need the end-user onboarding flow
    if current_role != USER_ROLE:
        ui.navigate.to('/')
        return

    if has_completed_onboarding():
        ui.navigate.to('/')
        return

    existing = get_onboarding_profile()

    state = {'step': 1}

    form = {
        'display_name': existing.get('display_name', ''),
        'support_tone': existing.get('support_tone', 'gentle'),
        'notification_mode': existing.get('notification_mode', 'balanced'),

        'noise_sensitivity': existing.get('noise_sensitivity', 3),
        'light_sensitivity': existing.get('light_sensitivity', 3),
        'crowd_sensitivity': existing.get('crowd_sensitivity', 3),
        'quiet_space_importance': existing.get('quiet_space_importance', 'high'),
        'trusted_contact_name': existing.get('trusted_contact_name', ''),

        'has_wearable': existing.get('has_wearable', False),
        'vibration_only': existing.get('vibration_only', True),
        'preferred_transport': existing.get('preferred_transport', 'walking'),
        'allow_aggregated_analytics': existing.get('allow_aggregated_analytics', True),
        'consent_confirmed': existing.get('consent_confirmed', False),
    }

    def set_value(key: str, value):
        form[key] = value
        render_step.refresh()
        render_summary.refresh()

    def step_chip(step_number: int) -> tuple[str, str]:
        if step_number == state['step']:
            return f'Step {step_number}', 'nm-onboarding-step-chip nm-onboarding-step-chip-active'
        if step_number < state['step']:
            return f'Step {step_number}', 'nm-onboarding-step-chip nm-onboarding-step-chip-done'
        return f'Step {step_number}', 'nm-onboarding-step-chip'

    def current_title() -> str:
        return {
            1: 'Tell us how to support you',
            2: 'Build your comfort profile',
            3: 'Set privacy and device preferences',
        }[state['step']]

    def current_subtitle() -> str:
        return {
            1: 'Let’s personalize the experience in a gentle way.',
            2: 'Help us understand what environments may feel harder to manage.',
            3: 'Choose how the app should behave and what can be used later by the backend.',
        }[state['step']]

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

    def finish_onboarding():
        if not form['consent_confirmed']:
            ui.notify('Please confirm the onboarding consent before continuing.', color='negative')
            return

        set_onboarding_profile(form.copy())
        set_onboarding_completed(True)
        ui.notify('Onboarding completed successfully', color='positive')
        ui.navigate.to('/')

    def section_title(title: str, subtitle: str | None = None):
        ui.label(title).classes('nm-field-title')
        if subtitle:
            ui.label(subtitle).classes('nm-field-subtitle')

    def slider_card(title: str, key: str, min_value: int, max_value: int, subtitle: str | None = None):
        with ui.card().classes('nm-onboarding-field-card w-full'):
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

    def choice_card(title: str, key: str, options: dict, subtitle: str | None = None):
        with ui.card().classes('nm-onboarding-field-card w-full'):
            section_title(title, subtitle)
            ui.toggle(
                options,
                value=form[key],
                on_change=lambda e, k=key: set_value(k, e.value),
            ).props('unelevated no-caps spread').classes('w-full mt-4')

    @ui.refreshable
    def render_header():
        with ui.column().classes('w-full gap-4 mb-6'):
            with ui.row().classes('w-full gap-2 flex-wrap'):
                for i in [1, 2, 3]:
                    text, classes = step_chip(i)
                    ui.label(text).classes(classes)

            ui.label(current_title()).classes('nm-page-title text-left')
            ui.label(current_subtitle()).classes('nm-subtitle text-[1.05rem]')

    @ui.refreshable
    def render_summary():
        with ui.card().classes('nm-onboarding-summary w-full lg:sticky lg:top-8'):
            ui.label('Your setup summary').classes('text-xl font-bold text-[#0B4A38]')
            ui.label('This information is kept temporarily in the frontend session for now.').classes('nm-small mt-1')

            with ui.column().classes('gap-4 mt-4'):
                with ui.card().classes('bg-white rounded-[20px] p-4 shadow-none border border-[#EEF3EF]'):
                    ui.label('Identity & support').classes('font-semibold text-[#0B4A38]')
                    ui.label(
                        f"Name: {form['display_name'] or '—'} · "
                        f"Tone: {form['support_tone']} · "
                        f"Notifications: {form['notification_mode']}"
                    ).classes('nm-small mt-1')

                with ui.card().classes('bg-white rounded-[20px] p-4 shadow-none border border-[#EEF3EF]'):
                    ui.label('Comfort profile').classes('font-semibold text-[#0B4A38]')
                    ui.label(
                        f"Noise {form['noise_sensitivity']} · "
                        f"Light {form['light_sensitivity']} · "
                        f"Crowd {form['crowd_sensitivity']}"
                    ).classes('nm-small mt-1')
                    ui.label(
                        f"Quiet space importance: {form['quiet_space_importance']}"
                    ).classes('nm-small mt-1')

                with ui.card().classes('bg-white rounded-[20px] p-4 shadow-none border border-[#EEF3EF]'):
                    ui.label('Privacy & device').classes('font-semibold text-[#0B4A38]')
                    ui.label(
                        f"Wearable: {'yes' if form['has_wearable'] else 'no'} · "
                        f"Vibration only: {'yes' if form['vibration_only'] else 'no'}"
                    ).classes('nm-small mt-1')
                    ui.label(
                        f"Aggregated analytics: {'allowed' if form['allow_aggregated_analytics'] else 'disabled'}"
                    ).classes('nm-small mt-1')

    @ui.refreshable
    def render_step():
        with ui.column().classes('w-full gap-5'):
            if state['step'] == 1:
                with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 gap-4'):
                    with ui.card().classes('nm-onboarding-field-card w-full'):
                        section_title('Display name', 'How should the app address you?')
                        ui.input(
                            'Display name',
                            value=form['display_name'],
                            on_change=lambda e: set_value('display_name', e.value),
                        ).props('outlined').classes('w-full mt-4')

                    choice_card(
                        'Support tone',
                        'support_tone',
                        {
                            'gentle': 'Gentle',
                            'neutral': 'Neutral',
                            'direct': 'Direct',
                        },
                        'Choose the style of prompts and messages',
                    )

                    choice_card(
                        'Notification style',
                        'notification_mode',
                        {
                            'minimal': 'Minimal',
                            'balanced': 'Balanced',
                            'proactive': 'Proactive',
                        },
                        'How often should support prompts appear?',
                    )

            elif state['step'] == 2:
                with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 gap-4'):
                    slider_card('Noise sensitivity', 'noise_sensitivity', 1, 5, '1 = low, 5 = very high')
                    slider_card('Light sensitivity', 'light_sensitivity', 1, 5, '1 = low, 5 = very high')
                    slider_card('Crowd sensitivity', 'crowd_sensitivity', 1, 5, '1 = low, 5 = very high')

                    choice_card(
                        'Quiet space importance',
                        'quiet_space_importance',
                        {
                            'low': 'Low',
                            'medium': 'Medium',
                            'high': 'High',
                        },
                        'How important is access to a calm space for recovery?',
                    )

                    with ui.card().classes('nm-onboarding-field-card w-full md:col-span-2'):
                        section_title('Trusted contact name', 'Optional — useful for future support flows')
                        ui.input(
                            'Trusted contact',
                            value=form['trusted_contact_name'],
                            on_change=lambda e: set_value('trusted_contact_name', e.value),
                        ).props('outlined').classes('w-full mt-4')

            elif state['step'] == 3:
                with ui.element('div').classes('grid grid-cols-1 md:grid-cols-2 gap-4'):
                    with ui.card().classes('nm-onboarding-field-card w-full'):
                        section_title('Connected wearable', 'Enable if a wearable may be used later')
                        ui.switch(
                            'Wearable available',
                            value=form['has_wearable'],
                            on_change=lambda e: set_value('has_wearable', e.value),
                        ).props('color=primary').classes('mt-4')

                    with ui.card().classes('nm-onboarding-field-card w-full'):
                        section_title('Vibration-only support')
                        ui.switch(
                            'Use vibration-only by default',
                            value=form['vibration_only'],
                            on_change=lambda e: set_value('vibration_only', e.value),
                        ).props('color=primary').classes('mt-4')

                    choice_card(
                        'Preferred transport',
                        'preferred_transport',
                        {
                            'walking': 'Walking',
                            'bus': 'Bus',
                            'metro': 'Metro',
                            'car': 'Car',
                            'train': 'Train',
                        },
                    )

                    with ui.card().classes('nm-onboarding-field-card w-full'):
                        section_title('Aggregated analytics consent')
                        ui.switch(
                            'Allow future aggregated analytics usage',
                            value=form['allow_aggregated_analytics'],
                            on_change=lambda e: set_value('allow_aggregated_analytics', e.value),
                        ).props('color=primary').classes('mt-4')
                        ui.label(
                            'This is only a frontend/session preference for now. '
                            'The backend will later handle real persistence and privacy logic.'
                        ).classes('nm-small mt-3')

                    with ui.card().classes('nm-onboarding-field-card w-full md:col-span-2'):
                        section_title('Consent confirmation')
                        ui.switch(
                            'I understand that this onboarding setup is currently stored temporarily in the frontend session',
                            value=form['consent_confirmed'],
                            on_change=lambda e: set_value('consent_confirmed', e.value),
                        ).props('color=primary').classes('mt-4')

            with ui.element('div').classes('nm-onboarding-actions'):
                with ui.card().classes('nm-surface-card w-full p-3'):
                    with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap'):
                        ui.button(
                            'Back',
                            on_click=go_back,
                        ).props('outline no-caps').classes('min-w-[120px]').set_visibility(state['step'] > 1)

                        with ui.row().classes('items-center gap-3 ml-auto'):
                            ui.button(
                                'Skip for now',
                                on_click=lambda: ui.navigate.to('/'),
                            ).props('flat no-caps').classes('min-w-[120px]')

                            if state['step'] < 3:
                                ui.button(
                                    'Next',
                                    on_click=go_next,
                                ).props('unelevated no-caps icon=arrow_forward').classes('min-w-[150px] nm-primary-btn')
                            else:
                                ui.button(
                                    'Finish onboarding',
                                    on_click=finish_onboarding,
                                ).props('unelevated no-caps icon=check_circle').classes('min-w-[190px] nm-primary-btn')

    with ui.column().classes('nm-shell nm-container w-full justify-center'):
        with ui.element('div').classes('nm-onboarding-shell'):
            with ui.element('div').classes('nm-onboarding-grid'):
                # LEFT SIDE HERO
                with ui.card().classes('nm-onboarding-hero w-full'):
                    ui.label('NeuroMove').classes('nm-onboarding-mini-title')
                    ui.label('Let’s create a calmer experience for you').classes('nm-onboarding-title mt-2')
                    ui.label(
                        'This onboarding helps the app adapt its tone, sensory assumptions, and default behavior. '
                        'It is intentionally lightweight and gentle.'
                    ).classes('nm-onboarding-subtitle mt-3')

                    with ui.element('div').classes('nm-onboarding-badge-row'):
                        with ui.row().classes('nm-onboarding-badge'):
                            ui.icon('shield')
                            ui.label('Privacy-first')
                        with ui.row().classes('nm-onboarding-badge'):
                            ui.icon('tune')
                            ui.label('Personalized setup')
                        with ui.row().classes('nm-onboarding-badge'):
                            ui.icon('smartphone')
                            ui.label('Responsive flow')

                    with ui.element('div').classes('nm-onboarding-orb-wrap'):
                        ui.element('div').classes('nm-onboarding-orb-glow')
                        with ui.element('div').classes('nm-onboarding-orb-ring'):
                            with ui.element('div').classes('nm-onboarding-orb-core'):
                                with ui.column().classes('items-center gap-2'):
                                    ui.icon('self_improvement').classes('text-white text-5xl')
                                    ui.label('SETUP').classes('text-white text-lg tracking-[0.22em] font-semibold')

                    with ui.card().classes('nm-onboarding-summary mt-6 shadow-none'):
                        ui.label('Why this matters').classes('text-lg font-bold text-[#0B4A38]')
                        with ui.column().classes('w-full gap-3 mt-4'):
                            with ui.row().classes('items-start gap-3'):
                                ui.icon('volume_up').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Sensory profile').classes('font-semibold')
                                    ui.label('Helps tailor future support around stimulation patterns.').classes('nm-small')

                            with ui.row().classes('items-start gap-3'):
                                ui.icon('vibration').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Support preferences').classes('font-semibold')
                                    ui.label('Improves the tone and style of future notifications.').classes('nm-small')

                            with ui.row().classes('items-start gap-3'):
                                ui.icon('privacy_tip').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Privacy setup').classes('font-semibold')
                                    ui.label('Prepares the future backend integration without overloading the user.').classes('nm-small')

                # RIGHT SIDE FORM
                with ui.card().classes('nm-onboarding-card w-full'):
                    render_header()
                    render_step()
                    render_summary()