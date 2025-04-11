# src/main.py
import logging
import threading
import time
import signal
import sys
from datetime import datetime

from src.failover.controller import FailoverController
from dashboard.app import create_app
from config.settings import DASHBOARD_HOST, DASHBOARD_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/network_failover_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

def start_dashboard():
    """Start the dashboard Flask app in a separate thread"""
    app = create_app()
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT)

def start_failover_controller():
    """Start the failover controller in the main thread"""
    controller = FailoverController()
    controller.start()

def handle_signal(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received, stopping application...")
    sys.exit(0)

def main():
    """Main entry point for the application"""
    logger.info("Starting Network Failover Automation System")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        # Start the dashboard in a separate thread
        dashboard_thread = threading.Thread(target=start_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        logger.info(f"Dashboard started at http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
        
        # Start the failover controller in the main thread
        start_failover_controller()
    
    except Exception as e:
        logger.error(f"Error in main application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()