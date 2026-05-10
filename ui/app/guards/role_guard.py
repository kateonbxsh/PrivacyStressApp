from nicegui import ui
from app.core.session import get_current_role, is_auth

def require_roles(*roles: str) -> bool:
    if not is_auth():
        ui.navigate.to('/login')
        return False

    current_role = get_current_role()
    allowed = {r.strip().lower() for r in roles}

    if current_role not in allowed:
        ui.notify(
            f'Access denied. Current role = {current_role}. Allowed = {", ".join(sorted(allowed))}',
            color='negative',
        )
        ui.navigate.to('/')
        return False

    return True
