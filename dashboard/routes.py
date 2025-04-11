# dashboard/routes.py
from flask import Blueprint, render_template, jsonify, request
from src.monitoring.persistence import MetricsDatabase
from config.settings import DB_PATH

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)
db = MetricsDatabase(DB_PATH)

@dashboard_bp.route('/detailed')
def detailed_view():
    """Render the detailed metrics view"""
    return render_template('detailed.html')

@dashboard_bp.route('/api/metrics/timeframe')
def get_metrics_timeframe():
    """Get metrics for a specific timeframe"""
    hours = request.args.get('hours', 24, type=int)
    interface = request.args.get('interface')
    
    # Initialize database if needed
    db.initialize()
    
    # Get metrics from database with timeframe filter
    metrics = db.get_metrics_by_timeframe(interface=interface, hours=hours)
    return jsonify(metrics)

@dashboard_bp.route('/api/interfaces')
def get_all_interfaces():
    """Get a list of all monitored interfaces"""
    db.initialize()
    
    # Query unique interfaces from the database
    interfaces = db.get_unique_interfaces()
    return jsonify(interfaces)

@dashboard_bp.route('/api/metrics/stats')
def get_metrics_stats():
    """Get statistical summary of metrics"""
    interface = request.args.get('interface')
    
    db.initialize()
    stats = db.get_metrics_statistics(interface=interface)
    return jsonify(stats)

def register_routes(app):
    """Register all routes with the Flask app"""
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
