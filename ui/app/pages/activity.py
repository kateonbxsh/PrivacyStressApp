from nicegui import ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.guards.auth_guard import require_auth
from app.services.activity_service import get_activity_history, get_latest_activity_entry
from app.theme import register_theme


def level_chip(level: str) -> tuple[str, str]:
    if level == 'high':
        return 'High', 'nm-chip nm-chip-high'
    if level == 'alert':
        return 'Alert', 'nm-chip nm-chip-alert'
    return 'Calm', 'nm-chip nm-chip-calm'


def activity_entry_card(entry: dict) -> None:
    chip_text, chip_classes = level_chip(entry['level'])

    with ui.card().classes('nm-activity-card w-full'):
        with ui.row().classes('w-full items-start justify-between gap-4 no-wrap'):
            with ui.row().classes('items-start gap-4 no-wrap'):
                with ui.avatar(color='#F1F7F3', text_color='primary').classes('shadow-none mt-1'):
                    ui.icon(entry.get('icon', 'spa'))

                with ui.column().classes('gap-1'):
                    ui.label(entry['title']).classes('text-lg font-bold text-[#0B4A38]')
                    ui.label(entry.get('subtitle', '')).classes('text-sm text-[#6E7687]')
                    ui.label(f"{entry.get('date', '')} {entry.get('time', '')}".strip()).classes('nm-activity-meta')

            ui.label(chip_text).classes(chip_classes)

        with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
            if entry.get('score') is not None:
                with ui.column().classes('nm-kpi-pill'):
                    ui.label('Score').classes('nm-kpi-label')
                    ui.label(str(entry['score'])).classes('nm-kpi-value')

            if entry.get('confidence') is not None:
                with ui.column().classes('nm-kpi-pill'):
                    ui.label('Confidence').classes('nm-kpi-label')
                    ui.label(str(entry['confidence'])).classes('nm-kpi-value')

        if entry.get('recommendation'):
            with ui.card().classes('nm-soft-surface p-4 mt-4 shadow-none'):
                ui.label('Recommendation').classes('text-sm font-semibold text-[#0B4A38]')
                ui.label(entry['recommendation']).classes('text-[0.96rem] text-[#4B5162] mt-1')


@ui.page('/activity')
def activity_page() -> None:
    register_theme()
    if not require_auth():
        return

    ui.element('div').classes('nm-hero-blur')

    history = get_activity_history()
    latest = get_latest_activity_entry()

    total_checkins = len(history)
    latest_level = latest['level'].title() if latest else '—'
    latest_score = latest.get('score', '—') if latest else '—'

    with screen_container():
        app_shell(active='activity')

        with ui.column().classes('w-full gap-2 mt-6'):
            ui.label('My activity').classes('nm-page-title')
            ui.label(
                'Recent check-ins and mock stress analysis results.'
            ).classes('nm-subtitle text-[1.05rem]')

        with ui.element('div').classes('grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-8 mt-6 items-start'):
            with ui.column().classes('w-full gap-4'):
                with ui.card().classes('nm-overview-card w-full'):
                    ui.label('Overview').classes('text-xl font-bold text-[#0B4A38]')
                    ui.label('A cleaner view of your recent check-ins.').classes('nm-small')

                    with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Check-ins').classes('nm-kpi-label')
                            ui.label(str(total_checkins)).classes('nm-kpi-value')

                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Latest level').classes('nm-kpi-label')
                            ui.label(str(latest_level)).classes('nm-kpi-value')

                        with ui.column().classes('nm-kpi-pill'):
                            ui.label('Latest score').classes('nm-kpi-label')
                            ui.label(str(latest_score)).classes('nm-kpi-value')

                if history:
                    for entry in history:
                        activity_entry_card(entry)
                else:
                    with ui.element('div').classes('nm-empty-state w-full'):
                        ui.icon('event_note').classes('text-primary text-3xl')
                        ui.label('No check-ins yet').classes('text-xl font-bold text-[#0B4A38]')
                        ui.label(
                            'Start your first check-in to build an activity history.'
                        ).classes('nm-small')
                        ui.button(
                            'Start check-in',
                            on_click=lambda: ui.navigate.to('/check-in')
                        ).props('unelevated no-caps icon=edit_note').classes('mt-2 nm-primary-btn')

            with ui.column().classes('w-full gap-4'):
                with ui.card().classes('nm-summary-card w-full lg:sticky lg:top-8'):
                    ui.label('Latest insight').classes('text-xl font-bold text-[#0B4A38]')

                    if latest:
                        ui.label(latest['title']).classes('text-lg font-bold mt-3')
                        ui.label(latest.get('subtitle', '')).classes('nm-small')

                        with ui.row().classes('w-full gap-3 mt-4 flex-wrap'):
                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Level').classes('nm-kpi-label')
                                ui.label(latest['level'].title()).classes('nm-kpi-value')

                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Score').classes('nm-kpi-label')
                                ui.label(str(latest.get('score', '—'))).classes('nm-kpi-value')

                            with ui.column().classes('nm-kpi-pill'):
                                ui.label('Confidence').classes('nm-kpi-label')
                                ui.label(str(latest.get('confidence', '—'))).classes('nm-kpi-value')

                        if latest.get('recommendation'):
                            with ui.card().classes('nm-soft-surface p-4 mt-5 shadow-none'):
                                ui.label('Recommendation').classes('text-sm font-semibold text-[#0B4A38]')
                                ui.label(latest['recommendation']).classes('text-[0.96rem] text-[#4B5162] mt-1')
                    else:
                        ui.label('No recent activity available.').classes('nm-small mt-3')

                with ui.card().classes('nm-summary-card w-full'):
                    ui.label('System note').classes('text-lg font-bold text-[#0B4A38]')
                    ui.label(
                        'This screen currently reads from a temporary UI session cache. '
                        'Later, the same page should fetch the history from the backend API and external database.'
                    ).classes('nm-small mt-2')

        ui.element('div').classes('h-24')
        bottom_nav('activity')
