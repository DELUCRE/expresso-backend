from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging
import os
import html
import re
import secrets

# Configurar logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expresso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurações de segurança - detectar ambiente
is_production = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SECURE'] = is_production  # HTTPS apenas em produção
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

db = SQLAlchemy(app)

# ============================================================================
# MODELOS DO BANCO DE DADOS
# ============================================================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Entrega(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    origem = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_entrega = db.Column(db.DateTime)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def init_db():
    """Inicializa o banco de dados"""
    try:
        db.create_all()
        
        # Criar usuário admin se não existir
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                ativo=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado com sucesso")
        else:
            print("Usuário admin já existe")
            
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/servicos')
def servicos():
    return render_template('servicos.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

# ============================================================================
# ROTAS DE GESTÃO
# ============================================================================

@app.route('/gestao')
def gestao_login():
    return render_template('gestao/login.html')

@app.route('/gestao/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validação básica
        if not username or not password:
            flash('Usuário e senha são obrigatórios', 'error')
            return redirect(url_for('gestao_login'))
        
        # Buscar usuário
        user = Usuario.query.filter_by(username=username, ativo=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('gestao_login'))
            
    except Exception as e:
        print(f"Erro no login: {e}")
        flash('Erro interno do servidor', 'error')
        return redirect(url_for('gestao_login'))

@app.route('/gestao/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('gestao_login'))
    
    # Estatísticas básicas
    total_entregas = Entrega.query.count()
    entregas_pendentes = Entrega.query.filter_by(status='pendente').count()
    entregas_entregues = Entrega.query.filter_by(status='entregue').count()
    
    return render_template('gestao/dashboard.html', 
                         total_entregas=total_entregas,
                         entregas_pendentes=entregas_pendentes,
                         entregas_entregues=entregas_entregues)

@app.route('/gestao/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('gestao_login'))

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/entregas', methods=['GET'])
def api_entregas():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    entregas = Entrega.query.all()
    return jsonify([{
        'id': e.id,
        'codigo': e.codigo,
        'origem': e.origem,
        'destino': e.destino,
        'status': e.status,
        'data_criacao': e.data_criacao.isoformat() if e.data_criacao else None
    } for e in entregas])

# ============================================================================
# HEADERS DE SEGURANÇA BÁSICOS
# ============================================================================

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Headers adicionais para produção
    if is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
    
    return response

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

# Inicializar banco automaticamente
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
