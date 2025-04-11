# dashboard/app.py
from flask import Flask, render_template, jsonify
import logging
import os

from src.monitoring.persistence import MetricsDatabase
from config.settings import DB_PATH

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configure app
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize database connection
    db = MetricsDatabase(DB_PATH)
    db.initialize()
    
    @app.route('/')
    def index():
        """Render the main dashboard page"""
        return render_template('index.html')
    
    @app.route('/api/metrics')
    def get_metrics():
        """API endpoint to get recent metrics"""
        metrics = db.get_recent_metrics(limit=100)
        return jsonify(metrics)
    
    @app.route('/api/metrics/<interface>')
    def get_interface_metrics(interface):
        """API endpoint to get metrics for a specific interface"""
        metrics = db.get_recent_metrics(interface=interface, limit=100)
        return jsonify(metrics)
    
    @app.route('/api/events')
    def get_events():
        """API endpoint to get recent failover events"""
        events = db.get_recent_failover_events()
        return jsonify(events)
    
    @app.route('/api/status')
    def get_status():
        """API endpoint to get current network status"""
        # Get most recent metric for each interface
        all_metrics = db.get_recent_metrics(limit=1000)
        
        # Group by interface and take the most recent for each
        interfaces = {}
        for metric in all_metrics:
            interface = metric['interface']
            if interface not in interfaces or metric['timestamp'] > interfaces[interface]['timestamp']:
                interfaces[interface] = metric
        
        # Get recent failover events
        events = db.get_recent_failover_events(limit=5)
        
        return jsonify({
            'interfaces': list(interfaces.values()),
            'recent_events': events
        })
    
    return app