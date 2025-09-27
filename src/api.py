#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import secrets
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permitir requisições de qualquer origem

app.secret_key = secrets.token_hex(16)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///expresso.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================================================
# MODELOS DO BANCO DE DADOS
# ============================================================================

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

class Entrega(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    origem = db.Column(db.String(100), nullable=False)
    destino = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = Usuario.query.filter_by(username=username, ativo=True).first()

    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            'success': True,
            'token': 'jwt_token_here',  # Placeholder for JWT
            'user': {'id': user.id, 'username': user.username}
        })

    return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

@app.route('/api/entregas', methods=['GET'])
def api_entregas():
    entregas = Entrega.query.all()
    return jsonify([{
        'id': e.id,
        'codigo': e.codigo,
        'origem': e.origem,
        'destino': e.destino,
        'status': e.status,
        'data_criacao': e.data_criacao.isoformat() if e.data_criacao else None
    } for e in entregas])

@app.route('/api/entregas', methods=['POST'])
def criar_entrega():
    data = request.get_json()
    entrega = Entrega(
        codigo=data['codigo'],
        origem=data['origem'],
        destino=data['destino']
    )
    db.session.add(entrega)
    db.session.commit()
    return jsonify({'success': True, 'id': entrega.id})

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def init_db():
    """Inicializa o banco de dados"""
    db.create_all()
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

