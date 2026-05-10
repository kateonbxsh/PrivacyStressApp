from fastapi import APIRouter
from nicegui import app, ui

from app.pages import home, activity, settings, help_page, login, form_page, admin_panel, onboarding  # noqa: F401

api_router = APIRouter(prefix='/api')


@api_router.get('/health')
def health() -> dict:
    return {'status': 'ok', 'service': 'neuromove-ui'}


@api_router.get('/state')
def state() -> dict:
    return {'mode': 'on_device', 'privacy': 'federated', 'risk_level': 'calm'}


app.include_router(api_router)

ui.run(
    title='NeuroMove',
    favicon='🛡️',
    reload=True,
    storage_secret='neuromove-dev-secret',
)
