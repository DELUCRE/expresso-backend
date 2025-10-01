"""
Health check routes - Rotas robustas para monitoramento Railway
"""

import os
import psutil
import shutil
from flask import Blueprint, jsonify
from datetime import datetime
from src.app import db, check_database, check_memory, check_disk

health_bp = Blueprint('health', __name__)

@health_bp.route('/')
def root():
    """Root health check - Resolve erro 502 do Railway"""
    return jsonify({
        'status': 'ok',
        'service': 'Expresso Itaporanga API',
        'version': '3.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'message': 'API funcionando corretamente'
    })

@health_bp.route('/health')
def health():
    """Health check detalhado com verificação de dependências"""
    
    # Verificações de saúde
    checks = {
        'database': check_database(),
        'memory': check_memory(),
        'disk': check_disk()
    }
    
    # Status geral
    all_healthy = all(checks.values())
    status = 'healthy' if all_healthy else 'unhealthy'
    status_code = 200 if all_healthy else 503
    
    # Informações do sistema
    try:
        memory_info = psutil.virtual_memory()
        disk_info = shutil.disk_usage('/')
        
        system_info = {
            'memory_percent': round(memory_info.percent, 2),
            'memory_available_gb': round(memory_info.available / (1024**3), 2),
            'disk_free_gb': round(disk_info.free / (1024**3), 2),
            'disk_total_gb': round(disk_info.total / (1024**3), 2)
        }
    except Exception:
        system_info = {'error': 'Could not retrieve system info'}
    
    response = {
        'status': status,
        'service': 'Expresso Itaporanga API',
        'version': '3.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'checks': checks,
        'system': system_info,
        'uptime': get_uptime()
    }
    
    return jsonify(response), status_code

@health_bp.route('/api/health')
def api_health():
    """Health check para endpoint da API"""
    return health()

@health_bp.route('/ready')
def ready():
    """Readiness probe - Verifica se a aplicação está pronta para receber tráfego"""
    
    # Verificações críticas para readiness
    ready_checks = {
        'database': check_database(),
        'models_loaded': check_models_loaded()
    }
    
    all_ready = all(ready_checks.values())
    status_code = 200 if all_ready else 503
    
    return jsonify({
        'ready': all_ready,
        'checks': ready_checks,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code

@health_bp.route('/live')
def live():
    """Liveness probe - Verifica se a aplicação está viva"""
    return jsonify({
        'alive': True,
        'timestamp': datetime.utcnow().isoformat(),
        'pid': os.getpid()
    })

def check_models_loaded():
    """Verificar se os modelos do SQLAlchemy foram carregados"""
    try:
        from src.app import Usuario, Entrega
        return True
    except Exception:
        return False

def get_uptime():
    """Calcular uptime da aplicação"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        create_time = process.create_time()
        uptime_seconds = datetime.now().timestamp() - create_time
        return round(uptime_seconds, 2)
    except Exception:
        return 0
