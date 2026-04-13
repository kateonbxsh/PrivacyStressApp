from nicegui import ui

from app.core.roles import ADMIN_ROLE, RESEARCHER_ROLE
from app.core.session import has_any_role


def app_shell(active: str, title: str = 'NeuroMove', show_device_badge: bool = True) -> None:
    with ui.row().classes('w-full items-center justify-between mb-4'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('shield').classes('text-lg text-primary')
            with ui.column().classes('gap-0'):
                ui.label(title).classes('text-2xl font-extrabold text-[#0B4A38] leading-none')
                ui.label('safe intelligence').classes('text-[11px] uppercase tracking-[0.18em] text-[#6E7687]')
        if show_device_badge:
            with ui.row().classes(
                'items-center gap-2 px-3 py-2 rounded-full bg-[#6BE6A8] text-[#0B4A38] font-semibold text-sm'
            ):
                ui.icon('lens_blur').classes('text-[10px]')
                ui.label('On Device')


def screen_container() -> ui.column:
    return ui.column().classes('nm-shell nm-container gap-0 w-full')


def bottom_nav(active: str) -> None:
    tabs = [
        ('home', 'Home', '/'),
        ('query_stats', 'Activity', '/activity'),
        ('settings', 'Settings', '/settings'),
    ]

    if has_any_role(ADMIN_ROLE, RESEARCHER_ROLE):
        tabs.append(('dashboard', 'Admin', '/admin'))

    with ui.element('div').classes('nm-bottom-bar'):
        with ui.row(wrap=False).classes('nm-bottom-bar-inner'):
            for icon, label, route in tabs:
                selected = active == label.lower()
                item_classes = 'nm-nav-item nm-nav-item-active' if selected else 'nm-nav-item'

                with ui.element('div').classes(item_classes).on(
                    'click',
                    lambda e, r=route: ui.navigate.to(r),
                ):
                    ui.icon(icon).classes('text-[20px]')
                    ui.label(label).classes('text-xs font-medium')