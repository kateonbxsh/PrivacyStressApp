from nicegui import ui

def status_chip(level: str) -> None:
    mapping = {'calm': ('Calm', 'nm-chip nm-chip-calm'), 'alert': ('Alert', 'nm-chip nm-chip-alert'), 'high': ('High', 'nm-chip nm-chip-high')}
    text, classes = mapping.get(level.lower(), (level.title(), 'nm-chip'))
    ui.label(text).classes(classes)

def soft_action(icon: str, title: str, subtitle: str, route: str) -> None:
    with ui.card().classes('w-full nm-card px-2 py-2'):
        with ui.button(on_click=lambda: ui.navigate.to(route)).props('flat no-caps').classes('w-full nm-soft-btn'):
            with ui.row().classes('w-full items-center justify-between no-wrap px-3'):
                with ui.row().classes('items-center gap-4 no-wrap'):
                    with ui.avatar(color='#F1F7F3', text_color='primary').classes('shadow-none'):
                        ui.icon(icon)
                    with ui.column().classes('gap-0'):
                        ui.label(title).classes('text-lg font-semibold text-[#0B6E53]')
                        ui.label(subtitle).classes('text-sm text-[#6E7687]')
                ui.icon('chevron_right').classes('text-[#A0A8B8]')
