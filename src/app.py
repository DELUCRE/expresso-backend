"""
Expresso Itaporanga - Backend API
Sistema de gestão de entregas e logística

Author: Expresso Itaporanga Team
Version: 2.0.0
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Configuração do banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Corrigir URL do PostgreSQL se necessário
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expresso.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Inicializar extensões
    db.init_app(app)
    
    # Configurar CORS
    CORS(app, 
         supports_credentials=True,
         origins=[
             'https://www.expressoitaporanga.com.br',
             'https://*.railway.app',
             'http://localhost:*'
         ])
    
    # Registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.api import api_bp
    from src.routes.health import health_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Middleware de segurança
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
    
    # Inicializar banco de dados
    with app.app_context():
        db.create_all()
        init_default_users()
    
    return app

# Inicializar SQLAlchemy
db = SQLAlchemy()

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
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    
    def __repr__(self):
        return f'<Entrega {self.codigo_rastreamento}>'
    
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

def init_default_users():
    """Inicializar usuários padrão"""
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
        logger.info("Usuários padrão inicializados")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar usuários: {e}")
        db.session.rollback()

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
