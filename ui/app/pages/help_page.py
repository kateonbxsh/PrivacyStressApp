from nicegui import ui
from app.components.cards import soft_action
from app.components.layout import screen_container
from app.theme import register_theme

@ui.page('/help')
def help_page() -> None:
    register_theme()
    ui.element('div').classes('nm-hero-blur')
    with screen_container().classes('justify-between'):
        ui.element('div').classes('h-4')
        with ui.column().classes('w-full items-center gap-4 mt-10'):
            with ui.element('div').classes('nm-stat-ring-outer !w-[300px] !h-[300px]'):
                with ui.element('div').classes('nm-stat-circle !w-[180px] !h-[180px]'):
                    ui.icon('air').classes('text-white text-6xl')
            ui.label('Take a breath').classes('nm-page-title text-[#0B6E53] text-center')
            ui.label('We are here to support you. Choose a safe path forward.').classes('nm-subtitle text-center text-[1.15rem] max-w-[320px]')
        with ui.column().classes('w-full gap-4 mt-6'):
            soft_action('call', 'Call my contact', 'Notify a trusted person', '/')
            soft_action('air', 'Breathing exercise', 'Start a guided 2-minute routine', '/')
            soft_action('home', 'Navigate home', 'Use the calmest route', '/')
        with ui.column().classes('w-full items-center mt-10 gap-5'):
            ui.link("I'm okay now", '/').classes('text-[#6E7687] no-underline text-base')
            ui.element('div').style('width:64px;height:8px;border-radius:999px;background:#E2E8E5;')
