from __future__ import annotations

USER_ROLE = 'user'
RESEARCHER_ROLE = 'researcher'
ADMIN_ROLE = 'admin'

ADMIN_PANEL_ROLES = {RESEARCHER_ROLE, ADMIN_ROLE}

def normalize_role(role: str | None) -> str:
    if not role:
        return USER_ROLE
    role = role.lower().strip()
    if role in {USER_ROLE, RESEARCHER_ROLE, ADMIN_ROLE}:
        return role
    return USER_ROLE


def is_admin_role(role: str | None) -> bool:
    return normalize_role(role) == ADMIN_ROLE

def can_access_admin_panel(role: str | None) -> bool:
    return normalize_role(role) in ADMIN_PANEL_ROLES

