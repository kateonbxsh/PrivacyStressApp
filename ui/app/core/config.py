import os 

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:4000/api')
MEC_API_URL = os.getenv('MEC_API_URL', 'http://localhost:8000')
MEC_REGION = os.getenv('MEC_REGION', 'local-demo')
MEC_NODE_NAME = os.getenv('MEC_NODE_NAME', 'MEC Local Docker')
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))
USE_MOCK_API = os.getenv('USE_MOCK_API', 'false').lower() == 'true'
USE_MOCK_ADMIN_ANALYTICS = os.getenv('USE_MOCK_ADMIN_ANALYTICS', 'false').lower() == 'true'
REQUEST_TIMEOUT = float(os.getenv('REQUEST_TIMEOUT', '10'))
