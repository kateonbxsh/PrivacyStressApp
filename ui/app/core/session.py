from __future__ import annotations
from nicegui import app
from app.core.roles import normalize_role

def set_aut_session(acces_token: str, user: dict) -> None:
    app.storage.user['authenticated'] = True
    app.storage.user['access_token'] = acces_token
    app.storage.user['user'] = user
    
    
def clear_auth_session() -> None:
    app.storage.user['authenticated'] = False
    app.storage.user.pop('access_token', None)
    app.storage.user.pop('user', None)
    
def is_auth() -> bool:
    return bool(app.storage.user.get('authenticated', False)) 
    
def get_access_token() -> str | None:
    return app.storage.user.get('acces_token')

def get_current_user() -> dict | None:
    return app.storage.user.get('user')

def get_current_role() -> str:
    user = get_current_user() or {}
    role = user.get('role','user')
    if not isinstance(role,str):
        return 'user'
    return role.strip().lower()

def has_any_role(*roles: str) -> bool:
    current_role = get_current_role()
    normalized_roles = [normalize_role(role) for role in roles]
    return current_role in normalized_roles

def has_completed_onboarding() -> bool:
    return bool(app.storage.user.get('onboarding_completed',False))

def set_onboarding_completed(value: bool = True) -> None:
    app.storage.user['onboarding_completed'] = value

def get_onboarding_profile() -> dict:
    profile = app.storage.user.get('onboarding_profile', {})
    return profile if isinstance(profile, dict) else {}

def set_onboarding_profile(profile: dict) -> None:
    app.storage.user['onboarding_profile'] = profile
