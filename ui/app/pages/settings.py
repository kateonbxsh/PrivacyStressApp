from nicegui import ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.guards.auth_guard import require_auth
from app.services.auth_service import logout
from app.services.mock_data import settings_state
from app.core.roles import USER_ROLE
from app.core.session import get_current_role
from app.theme import register_theme


@ui.page('/settings')
def settings_page() -> None:
    register_theme()
    if not require_auth():
        return

    state = settings_state()
    ui.element('div').classes('nm-hero-blur')

    async def handle_logout():
        await logout()
        ui.notify('Déconnexion réussie', color='positive')
        ui.navigate.to('/login')

    with screen_container():
        app_shell(active='settings')
        ui.label('Settings').classes('nm-page-title mt-6')
        ui.label('Manage your sanctuary and privacy preferences.').classes('nm-subtitle text-[1.05rem]')

        with ui.element('div').classes('nm-grid-cards mt-4'):
            with ui.column().classes('gap-6'):
                ui.label('Notifications').classes('nm-section-title')
                with ui.card().classes('nm-card p-5'):
                    with ui.row().classes('w-full items-center justify-between nm-setting-row'):
                        with ui.column().classes('gap-0'):
                            ui.label('Vibration only').classes('text-xl font-semibold')
                            ui.label('Gentle tactile feedback').classes('nm-small')
                        ui.switch(value=state['vibration_only']).props('color=primary')

                    ui.separator().classes('opacity-30')

                    with ui.row().classes('w-full items-center justify-between nm-setting-row'):
                        with ui.column().classes('gap-0'):
                            ui.label('Sound alerts').classes('text-xl font-semibold')
                            ui.label('Auditory notifications').classes('nm-small')
                        ui.switch(value=state['sound_alerts']).props('color=primary')

                ui.label('Trusted contacts').classes('nm-section-title mt-6')
                with ui.card().classes('nm-card p-5 gap-4'):
                    for contact in state['contacts']:
                        with ui.row().classes('w-full items-center justify-between'):
                            with ui.row().classes('items-center gap-4'):
                                ui.image(contact['image']).classes('w-14 h-14 rounded-full object-cover')
                                ui.label(contact['name']).classes('text-xl')
                            ui.icon('chevron_right').classes('text-[#A0A8B8]')

                    ui.button(
                        'Add contact',
                        icon='add_circle',
                        on_click=lambda: ui.notify('To be implemented'),
                    ).props('flat no-caps color=primary').classes('self-start')

            with ui.column().classes('gap-6'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('Privacy').classes('nm-section-title')
                    ui.label('PRIVATE SPACE').classes('nm-chip nm-chip-calm')

                with ui.card().classes('nm-card p-5'):
                    with ui.row().classes('w-full items-center justify-between nm-setting-row'):
                        with ui.column().classes('gap-0'):
                            ui.label('Federated Learning').classes('text-xl font-semibold')
                            ui.label('Your data never leaves your phone').classes('nm-small')
                        ui.switch(value=state['federated_learning']).props('color=primary')

                    with ui.card().classes('bg-[#FBFCFB] rounded-[22px] p-4 mt-3 shadow-none border border-[#EFF3F0]'):
                        ui.label(
                            'NeuroMove uses advanced on-device processing to ensure your neural patterns and activity logs remain encrypted and exclusive to your hardware.'
                        ).classes('text-[0.98rem] italic text-[#5D6575]')

                ui.label('About').classes('nm-section-title mt-6')
                with ui.card().classes('nm-card p-5'):
                    with ui.row().classes('w-full items-center justify-between'):
                        ui.label('Version').classes('text-xl')
                        ui.label(state['version']).classes('text-xl text-[#6E7687]')

                    ui.separator().classes('opacity-30 my-3')

                    with ui.row().classes('w-full items-center justify-between'):
                        ui.link('Privacy Policy', '#').classes('text-primary text-xl no-underline font-medium')
                        ui.icon('open_in_new').classes('text-primary')

        if get_current_role() == USER_ROLE:
            ui.button(
                'Edit onboarding',
                on_click=lambda: ui.navigate.to('/onboarding')
            ).props('outline no-caps icon=tune').classes('w-full lg:w-[240px] mt-4')
            
        ui.button(
            'Se déconnecter',
            on_click=handle_logout,
        ).props('unelevated no-caps').classes('w-full nm-primary-btn mt-6')

        ui.element('div').classes('h-24')
        bottom_nav('settings')
