from nicegui import app, ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.core.session import get_current_user, has_any_role
from app.guards.auth_guard import require_auth
from app.services.checkin_service import map_prediction_to_home_state
from app.services.mock_data import current_state
from app.theme import register_theme


def level_chip(level: str) -> tuple[str, str]:
    if level == 'high':
        return 'High', 'nm-chip nm-chip-high'
    if level == 'alert':
        return 'Alert', 'nm-chip nm-chip-alert'
    return 'Calm', 'nm-chip nm-chip-calm'


def hero_icon(level: str) -> str:
    if level == 'high':
        return 'priority_high'
    if level == 'alert':
        return 'visibility'
    return 'spa'


@ui.page('/')
def home_page() -> None:
    register_theme()
    if not require_auth():
        return

    user = get_current_user() or {}
    prediction = app.storage.user.get('last_prediction')
    last_checkin = app.storage.user.get('last_checkin')

    if prediction:
        state = map_prediction_to_home_state(prediction)
    else:
        state = current_state()

    ui.element('div').classes('nm-hero-blur')

    with screen_container():
        app_shell(active='home')

        if user.get('display_name'):
            ui.label(f"Hello, {user['display_name']}").classes('text-sm text-[#6E7687] mb-2')

        with ui.element('div').classes('grid grid-cols-1 xl:grid-cols-[1.08fr_0.92fr] gap-8 mt-6 items-start'):
            # LEFT SIDE: HERO
            with ui.column().classes('w-full gap-5'):
                with ui.card().classes('nm-home-hero w-full'):
                    with ui.element('div').classes('grid grid-cols-1 lg:grid-cols-[0.95fr_1.05fr] gap-8 items-center'):
                        # Visual orb
                        with ui.column().classes('items-center justify-center'):
                            with ui.element('div').classes('nm-home-orb-wrap'):
                                ui.element('div').classes('nm-home-orb-glow')

                                with ui.element('div').classes('nm-home-orb-ring'):
                                    with ui.element('div').classes('nm-home-orb-core'):
                                        with ui.column().classes('items-center gap-2'):
                                            ui.icon(hero_icon(state['level'])).classes('text-white text-5xl')
                                            ui.label(state['label'].upper()).classes(
                                                'text-white text-lg tracking-[0.22em] font-semibold'
                                            )

                        # Textual content
                        with ui.column().classes('justify-center gap-3'):
                            chip_text, chip_classes = level_chip(state['level'])

                            ui.label('Current state').classes('nm-home-mini-title')
                            ui.label(state['title']).classes('nm-page-title text-center lg:text-left')

                            ui.label(state['description']).classes(
                                'nm-subtitle text-center lg:text-left text-[1.15rem] lg:text-[1.28rem] leading-relaxed'
                            )

                            with ui.element('div').classes('nm-home-badge-row justify-center lg:justify-start'):
                                ui.label(chip_text).classes(chip_classes)
                                with ui.row().classes('nm-home-chip'):
                                    ui.icon('shield').classes('text-[16px]')
                                    ui.label('Privacy-first')
                                with ui.row().classes('nm-home-chip'):
                                    ui.icon('memory').classes('text-[16px]')
                                    ui.label('On-device ready')

                            with ui.element('div').classes('nm-home-cta-row'):
                                ui.button(
                                    'I need help',
                                    on_click=lambda: ui.navigate.to('/help')
                                ).props('unelevated no-caps icon=headset_mic').classes(
                                    'w-full sm:w-auto lg:w-[260px] nm-primary-btn'
                                )

                                ui.button(
                                    'Start check-in',
                                    on_click=lambda: ui.navigate.to('/check-in')
                                ).props('outline no-caps icon=edit_note').classes(
                                    'w-full sm:w-auto lg:w-[220px]'
                                )

                                if has_any_role('researcher', 'admin'):
                                    ui.button(
                                        'Open admin panel',
                                        on_click=lambda: ui.navigate.to('/admin')
                                    ).props('outline no-caps icon=dashboard').classes(
                                        'w-full sm:w-auto lg:w-[220px]'
                                    )

                # Secondary insight strip
                with ui.element('div').classes('nm-home-stat-grid'):
                    with ui.card().classes('nm-home-insight-card w-full'):
                        ui.label('Today').classes('nm-home-mini-title')
                        if prediction:
                            ui.label(prediction['stress_level'].title()).classes(
                                'text-2xl font-extrabold text-[#0B4A38] mt-1')
                            ui.label('Latest detected state').classes('nm-home-muted mt-1')
                        else:
                            ui.label('No check-in yet').classes('text-2xl font-extrabold text-[#0B4A38] mt-1')
                            ui.label('Start a check-in to generate an estimate').classes('nm-home-muted mt-1')

                    with ui.card().classes('nm-home-insight-card w-full'):
                        ui.label('Quick access').classes('nm-home-mini-title')
                        ui.label('Your next best action').classes('text-lg font-bold text-[#0B4A38] mt-1')
                        ui.label(
                            'Use a quick check-in to enrich context, then review your activity history.'
                        ).classes('nm-home-muted mt-1')

            # RIGHT SIDE: DETAILS / LAST ANALYSIS
            with ui.column().classes('w-full gap-5'):
                with ui.card().classes('nm-home-side-card w-full lg:sticky lg:top-8'):
                    ui.label('Latest analysis').classes('text-xl font-bold text-[#0B4A38]')

                    if prediction:
                        with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Score').classes('nm-kpi-label')
                                ui.label(str(prediction.get('score', '—'))).classes('nm-kpi-value')

                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Confidence').classes('nm-kpi-label')
                                ui.label(str(prediction.get('confidence', '—'))).classes('nm-kpi-value')

                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Level').classes('nm-kpi-label')
                                ui.label(prediction['stress_level'].title()).classes('nm-kpi-value')

                        with ui.card().classes('nm-home-reco mt-5 shadow-none'):
                            ui.label('Recommendation').classes('text-sm font-semibold text-[#0B4A38]')
                            ui.label(prediction['recommendation']).classes('text-[0.98rem] text-[#4B5162] mt-1')

                        if last_checkin:
                            env = last_checkin.get('environment', {})
                            user_ctx = last_checkin.get('user_context', {})

                            with ui.card().classes('nm-home-reco mt-4 shadow-none'):
                                ui.label('Latest context').classes('text-sm font-semibold text-[#0B4A38]')
                                ui.label(
                                    f"Noise {env.get('noise_level', '—')} · "
                                    f"Light {env.get('light_level', '—')} · "
                                    f"Crowd {env.get('crowd_density', '—')}"
                                ).classes('nm-home-muted mt-1')
                                ui.label(
                                    f"Energy {user_ctx.get('energy_level', '—')} · "
                                    f"Breathing {user_ctx.get('breathing_state', '—')}"
                                ).classes('nm-home-muted mt-1')
                    else:
                        ui.label(
                            'No prediction available yet. Complete a check-in to generate your first mock analysis.'
                        ).classes('nm-small mt-3')

                        ui.button(
                            'Start first check-in',
                            on_click=lambda: ui.navigate.to('/check-in')
                        ).props('unelevated no-caps icon=edit_note').classes('mt-4 nm-primary-btn')

                with ui.card().classes('nm-home-side-card w-full'):
                    ui.label('Journey').classes('text-xl font-bold text-[#0B4A38]')
                    ui.label(
                        'Your app flow is now structured around check-ins, results, and activity history.'
                    ).classes('nm-small mt-2')

                    with ui.column().classes('gap-3 mt-4'):
                        with ui.row().classes('items-start gap-3'):
                            ui.icon('login').classes('text-primary mt-1')
                            with ui.column().classes('gap-0'):
                                ui.label('Authentication').classes('font-semibold')
                                ui.label('User session starts from the login page.').classes('nm-small')

                        with ui.row().classes('items-start gap-3'):
                            ui.icon('edit_note').classes('text-primary mt-1')
                            with ui.column().classes('gap-0'):
                                ui.label('Check-in').classes('font-semibold')
                                ui.label('User completes a contextual self-report.').classes('nm-small')

                        with ui.row().classes('items-start gap-3'):
                            ui.icon('monitor_heart').classes('text-primary mt-1')
                            with ui.column().classes('gap-0'):
                                ui.label('Mock prediction').classes('font-semibold')
                                ui.label('Home displays the latest estimated state.').classes('nm-small')

                        with ui.row().classes('items-start gap-3'):
                            ui.icon('history').classes('text-primary mt-1')
                            with ui.column().classes('gap-0'):
                                ui.label('History').classes('font-semibold')
                                ui.label('Activity keeps a readable timeline of check-ins.').classes('nm-small')

        ui.element('div').classes('h-24')
        bottom_nav('home')
