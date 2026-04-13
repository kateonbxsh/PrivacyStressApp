import os 

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
USE_MOCK_API = 'true' == 'true' # os.getenv('USE_MOCK_API', 'true').lower()
REQUEST_TIMEOUT = float(os.getenv('REQUEST_TIMEOUT', '10'))