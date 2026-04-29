from nicegui import app, ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.core.roles import USER_ROLE
from app.core.session import (
    get_current_role,
    get_current_user,
    get_onboarding_profile,
    has_any_role,
    has_completed_onboarding,
    set_onboarding_completed,
    set_onboarding_profile,
)
from app.guards.auth_guard import require_auth
from app.services.activity_service import clear_activity_history_cache
from app.services.auth_service import logout
from app.theme import register_theme


@ui.page('/settings')
def settings_page() -> None:
    register_theme()
    if not require_auth():
        return

    current_role = get_current_role()
    user = get_current_user() or {}
    onboarding = get_onboarding_profile()

    if current_role == USER_ROLE and not has_completed_onboarding():
        ui.navigate.to('/onboarding')
        return

    profile = {
        'display_name': onboarding.get('display_name', user.get('display_name', '')),
        'support_tone': onboarding.get('support_tone', 'gentle'),
        'notification_mode': onboarding.get('notification_mode', 'balanced'),
        'noise_sensitivity': onboarding.get('noise_sensitivity', 3),
        'light_sensitivity': onboarding.get('light_sensitivity', 3),
        'crowd_sensitivity': onboarding.get('crowd_sensitivity', 3),
        'quiet_space_importance': onboarding.get('quiet_space_importance', 'high'),
        'trusted_contact_name': onboarding.get('trusted_contact_name', ''),
        'has_wearable': onboarding.get('has_wearable', False),
        'vibration_only': onboarding.get('vibration_only', True),
        'preferred_transport': onboarding.get('preferred_transport', 'walking'),
        'allow_aggregated_analytics': onboarding.get('allow_aggregated_analytics', True),
    }

    ui.element('div').classes('nm-hero-blur')

    def update_profile_field(key: str, value):
        profile[key] = value
        set_onboarding_profile(profile.copy())
        render_sidebar.refresh()

    def reset_mock_state():
        app.storage.user.pop('last_checkin', None)
        app.storage.user.pop('last_prediction', None)
        clear_activity_history_cache()
        ui.notify('Mock state reset', color='positive')

    def reset_onboarding():
        set_onboarding_profile({})
        set_onboarding_completed(False)
        ui.notify('Onboarding reset', color='positive')
        ui.navigate.to('/onboarding')

    async def handle_logout():
        await logout()
        ui.notify('Déconnexion réussie', color='positive')
        ui.navigate.to('/login')

    @ui.refreshable
    def render_sidebar():
        with ui.card().classes('nm-settings-card w-full lg:sticky lg:top-8'):
            ui.label('Profile summary').classes('text-xl font-bold text-[#0B4A38]')
            ui.label(
                'Your current support and comfort setup.'
            ).classes('nm-small mt-1')

            with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
                with ui.column().classes('nm-settings-stat'):
                    ui.label('Tone').classes('nm-settings-stat-label')
                    ui.label(profile['support_tone'].title()).classes('nm-settings-stat-value')

                with ui.column().classes('nm-settings-stat'):
                    ui.label('Notifications').classes('nm-settings-stat-label')
                    ui.label(profile['notification_mode'].title()).classes('nm-settings-stat-value')

                with ui.column().classes('nm-settings-stat'):
                    ui.label('Wearable').classes('nm-settings-stat-label')
                    ui.label('Yes' if profile['has_wearable'] else 'No').classes('nm-settings-stat-value')

            with ui.card().classes('nm-settings-soft mt-5 shadow-none'):
                ui.label('Comfort profile').classes('font-semibold text-[#0B4A38]')
                ui.label(
                    f"Noise {profile['noise_sensitivity']}/5 · "
                    f"Light {profile['light_sensitivity']}/5 · "
                    f"Crowd {profile['crowd_sensitivity']}/5"
                ).classes('nm-small mt-1')
                ui.label(
                    f"Quiet space importance: {profile['quiet_space_importance']}"
                ).classes('nm-small mt-1')

            with ui.card().classes('nm-settings-soft mt-4 shadow-none'):
                ui.label('Session note').classes('font-semibold text-[#0B4A38]')
                ui.label(
                    'These settings are currently stored in the frontend session/profile only. '
                    'Later they should be persisted by the backend and external database.'
                ).classes('nm-small mt-1')

    with screen_container():
        app_shell(active='settings')

        with ui.card().classes('nm-settings-hero w-full mt-6'):
            with ui.row().classes('w-full items-start justify-between gap-4 flex-wrap'):
                with ui.column().classes('gap-1'):
                    ui.label('Settings').classes('nm-page-title text-left')
                    ui.label(
                        'Manage your preferences, comfort profile, device settings, and privacy choices.'
                    ).classes('nm-subtitle text-[1.05rem]')
                    ui.label(
                        f"Signed in as {profile['display_name'] or user.get('display_name', 'Unknown')} · role: {current_role}"
                    ).classes('nm-small mt-2')

                with ui.row().classes('nm-profile-chip-row'):
                    if profile['vibration_only']:
                        with ui.row().classes('nm-profile-chip'):
                            ui.icon('vibration')
                            ui.label('Vibration-only')

                    if profile['has_wearable']:
                        with ui.row().classes('nm-profile-chip'):
                            ui.icon('watch')
                            ui.label('Wearable enabled')

                    with ui.row().classes('nm-profile-chip'):
                        ui.icon('privacy_tip')
                        ui.label(
                            'Aggregated analytics allowed'
                            if profile['allow_aggregated_analytics']
                            else 'Aggregated analytics disabled'
                        )

        with ui.element('div').classes('grid grid-cols-1 xl:grid-cols-[1.12fr_0.88fr] gap-8 mt-6 items-start'):
            # LEFT COLUMN
            with ui.column().classes('w-full gap-5'):
                with ui.card().classes('nm-settings-card w-full'):
                    ui.label('Identity & support preferences').classes('nm-settings-section-title')
                    ui.label(
                        'Adjust how the app addresses you and how it should communicate.'
                    ).classes('nm-settings-note mt-1')

                    with ui.element('div').classes('nm-settings-grid mt-5'):
                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Display name').classes('font-semibold text-[#0B4A38]')
                            ui.input(
                                'Display name',
                                value=profile['display_name'],
                                on_change=lambda e: update_profile_field('display_name', e.value),
                            ).props('outlined').classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Support tone').classes('font-semibold text-[#0B4A38]')
                            ui.toggle(
                                {
                                    'gentle': 'Gentle',
                                    'neutral': 'Neutral',
                                    'direct': 'Direct',
                                },
                                value=profile['support_tone'],
                                on_change=lambda e: update_profile_field('support_tone', e.value),
                            ).props('unelevated no-caps spread').classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none md:col-span-2'):
                            ui.label('Notification mode').classes('font-semibold text-[#0B4A38]')
                            ui.toggle(
                                {
                                    'minimal': 'Minimal',
                                    'balanced': 'Balanced',
                                    'proactive': 'Proactive',
                                },
                                value=profile['notification_mode'],
                                on_change=lambda e: update_profile_field('notification_mode', e.value),
                            ).props('unelevated no-caps spread').classes('w-full mt-4')

                with ui.card().classes('nm-settings-card w-full'):
                    ui.label('Comfort profile').classes('nm-settings-section-title')
                    ui.label(
                        'Refine the sensory assumptions used to personalize support.'
                    ).classes('nm-settings-note mt-1')

                    with ui.element('div').classes('nm-settings-grid mt-5'):
                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Noise sensitivity').classes('font-semibold text-[#0B4A38]')
                            noise_badge = ui.label(str(profile['noise_sensitivity'])).classes('nm-value-pill mt-2')
                            def on_noise(e):
                                update_profile_field('noise_sensitivity', e.value)
                                noise_badge.set_text(str(e.value))
                            ui.slider(min=1, max=5, value=profile['noise_sensitivity'], step=1, on_change=on_noise).classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Light sensitivity').classes('font-semibold text-[#0B4A38]')
                            light_badge = ui.label(str(profile['light_sensitivity'])).classes('nm-value-pill mt-2')
                            def on_light(e):
                                update_profile_field('light_sensitivity', e.value)
                                light_badge.set_text(str(e.value))
                            ui.slider(min=1, max=5, value=profile['light_sensitivity'], step=1, on_change=on_light).classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Crowd sensitivity').classes('font-semibold text-[#0B4A38]')
                            crowd_badge = ui.label(str(profile['crowd_sensitivity'])).classes('nm-value-pill mt-2')
                            def on_crowd(e):
                                update_profile_field('crowd_sensitivity', e.value)
                                crowd_badge.set_text(str(e.value))
                            ui.slider(min=1, max=5, value=profile['crowd_sensitivity'], step=1, on_change=on_crowd).classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Quiet-space importance').classes('font-semibold text-[#0B4A38]')
                            ui.toggle(
                                {
                                    'low': 'Low',
                                    'medium': 'Medium',
                                    'high': 'High',
                                },
                                value=profile['quiet_space_importance'],
                                on_change=lambda e: update_profile_field('quiet_space_importance', e.value),
                            ).props('unelevated no-caps spread').classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none md:col-span-2'):
                            ui.label('Trusted contact').classes('font-semibold text-[#0B4A38]')
                            ui.input(
                                'Trusted contact name',
                                value=profile['trusted_contact_name'],
                                on_change=lambda e: update_profile_field('trusted_contact_name', e.value),
                            ).props('outlined').classes('w-full mt-4')

                with ui.card().classes('nm-settings-card w-full'):
                    ui.label('Device & privacy').classes('nm-settings-section-title')
                    ui.label(
                        'Control how the app behaves on-device and what may be used later by backend analytics.'
                    ).classes('nm-settings-note mt-1')

                    with ui.element('div').classes('nm-settings-grid mt-5'):
                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Wearable support').classes('font-semibold text-[#0B4A38]')
                            ui.switch(
                                'Wearable available',
                                value=profile['has_wearable'],
                                on_change=lambda e: update_profile_field('has_wearable', e.value),
                            ).props('color=primary').classes('mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Default support mode').classes('font-semibold text-[#0B4A38]')
                            ui.switch(
                                'Use vibration-only by default',
                                value=profile['vibration_only'],
                                on_change=lambda e: update_profile_field('vibration_only', e.value),
                            ).props('color=primary').classes('mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Preferred transport').classes('font-semibold text-[#0B4A38]')
                            ui.select(
                                ['walking', 'bus', 'metro', 'car', 'train'],
                                value=profile['preferred_transport'],
                                on_change=lambda e: update_profile_field('preferred_transport', e.value),
                                label='Preferred transport',
                            ).props('outlined').classes('w-full mt-4')

                        with ui.card().classes('nm-settings-soft shadow-none'):
                            ui.label('Aggregated analytics consent').classes('font-semibold text-[#0B4A38]')
                            ui.switch(
                                'Allow future aggregated analytics usage',
                                value=profile['allow_aggregated_analytics'],
                                on_change=lambda e: update_profile_field('allow_aggregated_analytics', e.value),
                            ).props('color=primary').classes('mt-4')

            # RIGHT COLUMN
            with ui.column().classes('w-full gap-5'):
                render_sidebar()

                with ui.card().classes('nm-settings-card w-full'):
                    ui.label('Quick actions').classes('text-xl font-bold text-[#0B4A38]')
                    ui.label(
                        'Useful actions for profile, session, and testing during the MVP phase.'
                    ).classes('nm-small mt-1')

                    with ui.column().classes('w-full gap-3 mt-5'):
                        if current_role == USER_ROLE:
                            ui.button(
                                'Edit onboarding',
                                on_click=lambda: ui.navigate.to('/onboarding')
                            ).props('outline no-caps icon=tune').classes('w-full')

                        if has_any_role('researcher', 'admin'):
                            ui.button(
                                'Open admin panel',
                                on_click=lambda: ui.navigate.to('/admin')
                            ).props('outline no-caps icon=dashboard').classes('w-full')

                        ui.button(
                            'Reset mock state',
                            on_click=reset_mock_state
                        ).props('outline no-caps icon=restart_alt').classes('w-full')

                        if current_role == USER_ROLE:
                            ui.button(
                                'Reset onboarding',
                                on_click=reset_onboarding
                            ).props('outline no-caps icon=history').classes('w-full')

                        ui.button(
                            'Sign out',
                            on_click=handle_logout
                        ).props('unelevated no-caps icon=logout').classes('w-full nm-primary-btn')

        ui.element('div').classes('h-24')
        bottom_nav('settings')