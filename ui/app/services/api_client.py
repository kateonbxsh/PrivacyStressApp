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

    async def post(self, path: str, json: dict | None, token: str | None = None):
        if USE_MOCK_API:
            return await self._mock_post(path, json or {}, token)

        headers = {}

        if token:
            headers['Authorization'] = f'Bearer {token}'

        async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
        ) as client:
            response = await client.post(path, json=json, headers=headers)
            return self._handle_response(response)

    async def get(self, path: str, token: str | None = None):
        if USE_MOCK_API:
            return await self._mock_get(path, token)

        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
        ) as client:
            response = await client.get(path, headers=headers)
            return self._handle_response(response)

    def _handle_response(self, response: httpx.Response):
        if response.status_code >= 400:
            try:
                payload = response.json()
                detail = payload.get('detail', 'Erreur API')
            except Exception:
                detail = response.text or 'Erreur API'
            raise APIError(detail, response.status_code)

        if not response.context:
            return None
        return response.json()

    # ---------------
    # MOCK MODE 
    # ---------------

    async def _mock_post(self, path: str, payload: dict, token: str | None):
        # print("bbbbbbBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\n\n\n")
        # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n\n")
        # print(path)

        if path == 'auth/login':
            email = payload.get('email')
            password = payload.get('password')

            if email == 'demo@neuromove.app' and password == 'demo123':
                return {
                    'access_token': 'mock-access-token-user',
                    'token_type': 'bearer',
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
                    'token_type': 'bearer',
                    'user': {
                        'id': 2,
                        'email': 'research@neuromove.app',
                        'display_name': 'Research Demo',
                        'role': 'researcher',
                    },
                }

            if email == 'admin@neuromove.app' and password == 'admin123':
                return {
                    'access_token': 'mock-access-token-admin',
                    'token_type': 'bearer',
                    'user': {
                        'id': 3,
                        'email': 'admin@neuromove.app',
                        'display_name': 'Admin Demo',
                        'role': 'admin',
                    },
                }

            raise APIError('Identifiants invalides', 401)

        if path == 'auth/logout':
            return None

        raise APIError(f'Route mock non implémentée: {path}', 404)

    async def _mock_get(self, path: str, token: str | None):
        if path == '/auth/me':
            if token == 'mock-access-token-user':
                return {
                    'id': 1,
                    'email': 'demo@neuromove.app',
                    'display_name': 'Demo User',
                    'role': 'user',
                }

            if token == 'mock-access-token-researcher':
                return {
                    'id': 2,
                    'email': 'research@neuromove.app',
                    'display_name': 'Research Demo',
                    'role': 'researcher',
                }

            if token == 'mock-access-token-admin':
                return {
                    'id': 3,
                    'email': 'admin@neuromove.app',
                    'display_name': 'Admin Demo',
                    'role': 'admin',
                }

            raise APIError('Session invalide ou expirée', 401)

        raise APIError(f'Route mock non implémentée: {path}', 404)


api_client = APIClient()
