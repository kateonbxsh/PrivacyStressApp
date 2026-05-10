from nicegui import ui
from app.components.cards import status_chip

def event_icon(level: str) -> tuple[str, str]:
    if level == 'high':
        return 'trip_origin', '#D84C4C'
    if level == 'alert':
        return 'change_history', '#996300'
    return 'circle', '#0B8A66'

def timeline_event(title: str, time: str, icon: str, level: str, suggestion: str | None = None) -> None:
    glyph, color = event_icon(level)
    with ui.row().classes('w-full gap-4 items-start no-wrap'):
        with ui.column().classes('items-center gap-0 shrink-0'):
            with ui.element('div').classes('nm-timeline-badge'):
                ui.icon(glyph).style(f'color:{color}; font-size: 28px;')
            ui.element('div').classes('nm-divider-line')
        with ui.column().classes('w-full gap-2 pt-2'):
            with ui.row().classes('w-full items-center justify-between no-wrap gap-2'):
                with ui.column().classes('gap-0'):
                    ui.label(title).classes('text-2xl font-bold leading-tight')
                    with ui.row().classes('items-center gap-2 text-[#6E7687]'):
                        ui.icon(icon).classes('text-[16px]')
                        ui.label(time).classes('text-base')
                status_chip(level)
            if suggestion:
                with ui.card().classes('nm-card mt-1 p-4'):
                    ui.label(suggestion).classes('text-[1rem] italic text-[#4B5162]')
