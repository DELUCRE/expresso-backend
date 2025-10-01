"""
Expresso Itaporanga - Backend API
Sistema de gestão de entregas e logística

Author: Expresso Itaporanga Team
Version: 3.0.0
"""

import os
import sys
import logging
import psutil
import shutil
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash

# Configuração de logging estruturado para Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Inicializar SQLAlchemy
db = SQLAlchemy()

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['VERSION'] = '3.0.0'
    
    # Configuração do banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Corrigir URL do PostgreSQL se necessário
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        logger.info(f"Using PostgreSQL database")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expresso.db'
        logger.info("Using SQLite database")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 5)),
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
        'pool_timeout': 30
    }
    
    # Inicializar extensões
    db.init_app(app)
    
    # Configurar CORS
    CORS(app, 
         supports_credentials=True,
         origins=[
             'https://www.expressoitaporanga.com.br',
             'https://*.railway.app',
             'http://localhost:*',
             'https://*.up.railway.app'
         ])
    
    # Registrar blueprints
    from src.routes.health import health_bp
    from src.routes.auth import auth_bp
    from src.routes.api import api_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Middleware de logging
    @app.before_request
    def log_request():
        logger.info(f"Request: {request.method} {request.path} - User-Agent: {request.user_agent.string[:100]}")
    
    @app.after_request
    def log_response(response):
        logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
        return response
    
    # Middleware de segurança
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Cache headers
        if request.endpoint == 'static':
            response.cache_control.max_age = 86400  # 1 day
        elif 'health' in str(request.endpoint):
            response.cache_control.no_cache = True
        elif 'api' in str(request.endpoint):
            response.cache_control.max_age = 300  # 5 minutes
            
        return response
    
    # Tratamento de erros
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 error for {request.path}")
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error for {request.path}: {str(error)}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    # Inicializar banco de dados
    with app.app_context():
        try:
            db.create_all()
            init_default_data()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    return app

# Modelos
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    perfil = db.Column(db.String(20), default='operador', nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ultimo_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

class Entrega(db.Model):
    __tablename__ = 'entregas'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_rastreamento = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Remetente
    remetente_nome = db.Column(db.String(100), nullable=False)
    remetente_endereco = db.Column(db.Text, nullable=False)
    remetente_cidade = db.Column(db.String(100), nullable=False)
    remetente_telefone = db.Column(db.String(20))
    
    # Destinatário
    destinatario_nome = db.Column(db.String(100), nullable=False)
    destinatario_endereco = db.Column(db.Text, nullable=False)
    destinatario_cidade = db.Column(db.String(100), nullable=False)
    destinatario_telefone = db.Column(db.String(20))
    
    # Produto
    tipo_produto = db.Column(db.String(50), nullable=False)
    peso = db.Column(db.Float)
    valor_declarado = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='pendente', nullable=False, index=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('entregas', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_rastreamento': self.codigo_rastreamento,
            'remetente_nome': self.remetente_nome,
            'remetente_cidade': self.remetente_cidade,
            'destinatario_nome': self.destinatario_nome,
            'destinatario_cidade': self.destinatario_cidade,
            'tipo_produto': self.tipo_produto,
            'status': self.status,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

def init_default_data():
    """Inicializar dados padrão"""
    try:
        # Admin
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                perfil='admin'
            )
            db.session.add(admin)
        
        # Operador
        if not Usuario.query.filter_by(username='operador').first():
            operador = Usuario(
                username='operador',
                password_hash=generate_password_hash('operador123'),
                perfil='operador'
            )
            db.session.add(operador)
        
        db.session.commit()
        logger.info("Default users initialized")
        
    except Exception as e:
        logger.error(f"Error initializing default data: {e}")
        db.session.rollback()

# Health check functions
def check_database():
    """Verificar conexão com banco de dados"""
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def check_memory():
    """Verificar uso de memória"""
    try:
        memory = psutil.virtual_memory()
        return memory.percent < 90
    except Exception:
        return True  # Se não conseguir verificar, assume OK

def check_disk():
    """Verificar espaço em disco"""
    try:
        disk = shutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        return free_percent > 10
    except Exception:
        return True  # Se não conseguir verificar, assume OK

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Expresso Itaporanga API v{app.config['VERSION']} on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
