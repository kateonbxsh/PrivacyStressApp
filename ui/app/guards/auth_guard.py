from nicegui import ui

from app.core.session import is_auth

def require_auth() -> bool: 
    if not is_auth():
        ui.navigate.to('/login')
        return False
    return True

