# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MikroTik router configuration
ROUTER_CONFIG = {
    'host': os.getenv('MIKROTIK_HOST', '192.168.88.1'),
    'username': os.getenv('MIKROTIK_USER', 'admin'),
    'password': os.getenv('MIKROTIK_PASSWORD', 'password'),
    'port': int(os.getenv('MIKROTIK_PORT', 8728)),
}

# Interface configuration
PRIMARY_INTERFACE = os.getenv('PRIMARY_INTERFACE', 'ether1')
SECONDARY_INTERFACES = os.getenv('SECONDARY_INTERFACES', 'ether2,ether3').split(',')

# Monitoring settings
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', 5))  # seconds
PING_COUNT = int(os.getenv('PING_COUNT', 5))
PING_TIMEOUT = int(os.getenv('PING_TIMEOUT', 1))  # seconds

# Thresholds
MAX_LATENCY = float(os.getenv('MAX_LATENCY', 100))  # milliseconds
MAX_PACKET_LOSS = float(os.getenv('MAX_PACKET_LOSS', 5))  # percentage

# Database settings
DB_PATH = os.getenv('DB_PATH', './data/metrics.db')

# AI model settings
MODEL_PATH = os.getenv('MODEL_PATH', './models/failover_model.pkl')
FEATURES = ['latency', 'packet_loss', 'bandwidth_usage', 'time_of_day']

# Dashboard settings
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))