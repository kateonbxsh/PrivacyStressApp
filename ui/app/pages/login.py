from nicegui import ui

from app.core.session import is_auth
from app.services.api_client import APIError
from app.services.auth_service import login
from app.theme import register_theme


@ui.page('/login')
def login_page() -> None:
    register_theme()

    if is_auth():
        ui.navigate.to('/')
        return

    ui.element('div').classes()
    ui.element('div').classes('nm-hero-blur')

    with ui.column().classes('nm-shell justify-center gap-5'):
        ui.label('Welcome back').classes('nm-page-title')
        ui.label('Sign in to continue with NeuroMove.').classes('nm-subtitle text-[1.05rem]')

        email = ui.input('Email').props('outlined type=email').classes('w-full')
        password = ui.input('Password', password=True, password_toggle_button=True).props('outlined').classes('w-full')

        async def handle_login():
            try:
                await login(email.value.strip(), password.value)
                ui.notify('Connexion réussie', color='positive')
                ui.navigate.to('/')
            except APIError as e:
                ui.notify(e.msg, color='negative')

        ui.button(
            'Se connecter',
            on_click=handle_login,
        ).props('unelevated no-caps').classes('w-full nm-primary-btn')

        with ui.card().classes('nm-card p-4 mt-4'):
            ui.label('Demo accounts').classes('text-lg font-bold')
            ui.label('User → demo@neuromove.app / demo123').classes('nm-small')
            ui.label('Researcher → research@neuromove.app / research123').classes('nm-small')
            ui.label('Admin → admin@neuromove.app / admin123').classes('nm-small')
