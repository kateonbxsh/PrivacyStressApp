import httpx

from app.core.config import API_BASE_URL, REQUEST_TIMEOUT, USE_MOCK_API


class APIError(Exception):
    def __init__(self, msg: str, status_code: int | None = None):
        super().__init__(msg)
        self.msg = msg
        self.status_code = status_code


class APIClient:
    def __init__(self) -> None:
        self.base_url = API_BASE_URL
        self.timeout = REQUEST_TIMEOUT

    async def post(self, path: str, json: dict | None = None, token: str | None = None):
        if USE_MOCK_API:
            return await self._mock_post(path, json or {}, token)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, follow_redirects=True) as client:
            response = await client.post(self._path(path), json=json, headers=self._headers(token))
            return self._handle_response(response)

    async def get(self, path: str, token: str | None = None):
        if USE_MOCK_API:
            return await self._mock_get(path, token)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(self._path(path), headers=self._headers(token))
            return self._handle_response(response)

    async def delete(self, path: str, token: str | None = None):
        if USE_MOCK_API:
            return None

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, follow_redirects=True) as client:
            response = await client.delete(self._path(path), headers=self._headers(token))
            return self._handle_response(response)

    def _path(self, path: str) -> str:
        return path if path.startswith('/') else f'/{path}'

    def _headers(self, token: str | None = None) -> dict:
        if not token:
            return {}
        if token.startswith('connect.sid='):
            return {'Cookie': token}
        return {'Authorization': f'Bearer {token}'}

    def _handle_response(self, response: httpx.Response):
        if response.status_code >= 400:
            try:
                payload = response.json()
                detail = payload.get('error') or payload.get('detail') or 'API error'
            except Exception:
                detail = response.text or 'API error'
            raise APIError(detail, response.status_code)

        if not response.content:
            return None

        data = response.json()
        cookie = response.headers.get('set-cookie')
        if isinstance(data, dict) and cookie:
            data['_session_cookie'] = cookie.split(';', 1)[0]
        return data

    async def _mock_post(self, path: str, payload: dict, token: str | None):
        if path in ('auth/login', '/auth/login'):
            email = payload.get('email')
            password = payload.get('password')

            if email == 'demo@neuromove.app' and password in ('demo123', 'demo12345'):
                return {
                    'access_token': 'mock-access-token-user',
                    'user': {
                        'id': 1,
                        'email': 'demo@neuromove.app',
                        'display_name': 'Demo User',
                        'role': 'user',
                    },
                }

            if email == 'research@neuromove.app' and password == 'research123':
                return {
                    'access_token': 'mock-access-token-researcher',
                    'user': {
                        'id': 2,
                        'email': 'research@neuromove.app',
                        'display_name': 'Research Demo',
                        'role': 'researcher',
                    },
                }

            if email == 'admin@neuromove.app' and password in ('admin123', 'admin12345'):
                return {
                    'access_token': 'mock-access-token-admin',
                    'user': {
                        'id': 3,
                        'email': 'admin@neuromove.app',
                        'display_name': 'Admin Demo',
                        'role': 'admin',
                    },
                }

            raise APIError('Invalid credentials', 401)

        if path in ('auth/logout', '/auth/logout'):
            return None

        raise APIError(f'Mock route not implemented: {path}', 404)

    async def _mock_get(self, path: str, token: str | None):
        if path in ('auth/me', '/auth/me', 'auth/session', '/auth/session'):
            if token == 'mock-access-token-user':
                return {'id': 1, 'email': 'demo@neuromove.app', 'display_name': 'Demo User', 'role': 'user'}
            if token == 'mock-access-token-researcher':
                return {'id': 2, 'email': 'research@neuromove.app', 'display_name': 'Research Demo', 'role': 'researcher'}
            if token == 'mock-access-token-admin':
                return {'id': 3, 'email': 'admin@neuromove.app', 'display_name': 'Admin Demo', 'role': 'admin'}
            raise APIError('Invalid or expired session', 401)

        raise APIError(f'Mock route not implemented: {path}', 404)


api_client = APIClient()
