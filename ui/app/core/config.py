import os 

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
USE_MOCK_API = os.getenv('USE_MOCK_API', 'true').lower() == 'true' # os.getenv('USE_MOCK_API', 'true').lower()
USE_MOCK_ADMIN_ANALYTICS = os.getenv('USE_MOCK_ADMIN_ANALYTICS', 'true').lower() == 'true'
REQUEST_TIMEOUT = float(os.getenv('REQUEST_TIMEOUT', '10'))
