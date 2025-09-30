"""
Health check routes
"""

from flask import Blueprint, jsonify
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/')
def root():
    """Root health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Expresso Itaporanga API',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

@health_bp.route('/health')
def health():
    """Detailed health check"""
    from src.app import db
    
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'service': 'Expresso Itaporanga API',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

@health_bp.route('/api/health')
def api_health():
    """API health check"""
    return health()
