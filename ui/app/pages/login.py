from nicegui import ui

from app.core.roles import USER_ROLE
from app.core.session import is_auth, get_current_role, has_completed_onboarding
from app.services.api_client import APIError
from app.services.auth_service import login
from app.theme import register_theme


@ui.page('/login')
def login_page() -> None:
    register_theme()

    if is_auth():
        ui.navigate.to('/')
        return

    ui.element('div').classes('nm-hero-blur')

    with ui.column().classes('nm-shell nm-container w-full justify-center'):
        with ui.element('div').classes('nm-login-shell'):
            with ui.element('div').classes('nm-login-grid'):
                # LEFT SIDE — HERO / BRAND
                with ui.card().classes('nm-login-hero w-full'):
                    ui.label('NeuroMove').classes('nm-login-mini-title')
                    ui.label('A calm, privacy-first stress support experience').classes('nm-login-title mt-2')
                    ui.label(
                        'Sign in to access your personal check-ins, activity history, and stress support tools. '
                        'The interface is designed to stay gentle, readable, and responsive across devices.'
                    ).classes('nm-login-subtitle mt-3')

                    with ui.element('div').classes('nm-login-badge-row'):
                        with ui.row().classes('nm-login-badge'):
                            ui.icon('shield')
                            ui.label('Privacy-first')
                        with ui.row().classes('nm-login-badge'):
                            ui.icon('memory')
                            ui.label('Federated-ready')
                        with ui.row().classes('nm-login-badge'):
                            ui.icon('smartphone')
                            ui.label('Responsive UI')

                    with ui.element('div').classes('nm-login-orb-wrap'):
                        ui.element('div').classes('nm-login-orb-glow')
                        with ui.element('div').classes('nm-login-orb-ring'):
                            with ui.element('div').classes('nm-login-orb-core'):
                                with ui.column().classes('items-center gap-2'):
                                    ui.icon('spa').classes('text-white text-5xl')
                                    ui.label('CALM').classes('text-white text-lg tracking-[0.22em] font-semibold')

                    with ui.card().classes('nm-login-demo-card mt-6 shadow-none'):
                        ui.label('What you can access after login').classes('text-lg font-bold text-[#0B4A38]')
                        with ui.column().classes('w-full gap-3 mt-4'):
                            with ui.row().classes('items-start gap-3'):
                                ui.icon('edit_note').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Check-in flow').classes('font-semibold')
                                    ui.label('Capture internal state, context, and support signals.').classes('nm-small')

                            with ui.row().classes('items-start gap-3'):
                                ui.icon('monitor_heart').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Latest analysis').classes('font-semibold')
                                    ui.label('Review the most recent stress estimate and recommendation.').classes('nm-small')

                            with ui.row().classes('items-start gap-3'):
                                ui.icon('history').classes('text-primary mt-1')
                                with ui.column().classes('gap-0'):
                                    ui.label('Activity history').classes('font-semibold')
                                    ui.label('Track recent check-ins and support events.').classes('nm-small')

                # RIGHT SIDE — LOGIN CARD
                with ui.card().classes('nm-login-card w-full self-center'):
                    ui.label('Welcome back').classes('nm-page-title')
                    ui.label('Sign in to continue with NeuroMove.').classes('nm-subtitle text-[1.05rem]')

                    email = ui.input('Email').props('outlined type=email').classes('w-full mt-5')
                    password = ui.input(
                        'Password',
                        password=True,
                        password_toggle_button=True,
                    ).props('outlined').classes('w-full mt-3')

                    login_button = ui.button(
                        'Sign in',
                        on_click=None,
                    ).props('unelevated no-caps icon=login').classes('w-full nm-primary-btn mt-5')

                    async def handle_login():
                        login_button.disable()
                        try:
                            await login(email.value.strip(), password.value)
                            ui.notify('Connexion réussie', color='positive')
                            
                            if get_current_role() == USER_ROLE and not has_completed_onboarding():
                                ui.navigate.to('/onboarding')
                            else:
                                ui.navigate.to('/')

                        except APIError as e:
                            ui.notify(getattr(e, 'msg', 'Authentication failed'), color='negative')
                        finally:
                            login_button.enable()

                    login_button.on('click', handle_login)

                    with ui.element('div').classes('nm-login-actions'):
                        ui.button(
                            'Need help?',
                            on_click=lambda: ui.navigate.to('/help'),
                        ).props('outline no-caps icon=headset_mic').classes('w-full sm:w-auto')

                        ui.button(
                            'Back to home',
                            on_click=lambda: ui.navigate.to('/'),
                        ).props('flat no-caps icon=home').classes('w-full sm:w-auto')

                    with ui.card().classes('nm-login-demo-card mt-6 shadow-none'):
                        ui.label('Demo accounts').classes('text-lg font-bold text-[#0B4A38]')
                        ui.label(
                            'Use these accounts to test the role-based experience.'
                        ).classes('nm-small mt-1')

                        with ui.column().classes('w-full gap-3 mt-4'):
                            with ui.card().classes('nm-login-demo-item shadow-none'):
                                ui.label('User').classes('font-semibold text-[#0B4A38]')
                                ui.label('demo@neuromove.app / demo12345').classes('nm-small')

                            with ui.card().classes('nm-login-demo-item shadow-none'):
                                ui.label('Researcher').classes('font-semibold text-[#0B4A38]')
                                ui.label('research@neuromove.app / research123').classes('nm-small')

                            with ui.card().classes('nm-login-demo-item shadow-none'):
                                ui.label('Admin').classes('font-semibold text-[#0B4A38]')
                                ui.label('admin@neuromove.app / admin12345').classes('nm-small')
