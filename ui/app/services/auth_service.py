from app.core.session import (
    clear_auth_session,
    get_access_token,
    get_session_cookie,
    set_aut_session
)

from app.services.api_client import api_client, APIError

async def login(email: str, pwd: str) -> dict:
    payload = {'email': email, 'password': pwd}
    data = await api_client.post('auth/login', json=payload)

    user = data.get('user') or {
        'id': data.get('userId'),
        'email': data.get('email'),
        'display_name': data.get('displayName') or data.get('email', '').split('@')[0],
        'role': data.get('role', 'user'),
        'profile_vector': data.get('recoveredVector'),
    }
    access_token = data.get('access_token') or data.get('_session_cookie') or 'backend-session'

    set_aut_session(access_token, user, data.get('_session_cookie'))
    return user

async def fetch_me() -> dict:
    token = get_session_cookie() or get_access_token()
    if not token:
        raise APIError('Aucun token disponible', 401)
    
    data = await api_client.get('auth/session', token=token)
    user = data.get('user') or {
        'id': data.get('userId'),
        'email': data.get('email'),
        'display_name': data.get('displayName') or data.get('email', '').split('@')[0],
        'role': data.get('role', 'user'),
        'profile_vector': data.get('recoveredVector'),
    }
    set_aut_session(token, user, token if token.startswith('connect.sid=') else None)
    return user

async def logout() -> None:
    token = get_session_cookie() or get_access_token()
    if token:
        try:
            await api_client.post('auth/logout', token=token)
        except APIError:
            pass
        
    clear_auth_session()
