from app.core.session import (
    clear_auth_session,
    get_access_token,
    set_aut_session
)

from app.services.api_client import api_client, APIError

async def login(email: str, pwd: str) -> dict:
    payload = {'email': email, 'password': pwd}
    data = await api_client.post('auth/login', json=payload)
    
    access_token = data['access_token']
    user = data['user']
    
    set_aut_session(access_token, user)
    return user

async def fetch_me() -> dict:
    token = get_access_token()
    if not token:
        raise APIError('Aucun token disponible', 401)
    
    user = await api_client.get('auth/me', token=token)
    set_aut_session(token,user)
    return user

async def logout() -> None:
    token = get_access_token()
    if token:
        try:
            await api_client.post('auth/logout', token=token)
        except APIError:
            pass
        
    clear_auth_session()