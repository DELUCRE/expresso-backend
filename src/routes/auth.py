"""
Authentication routes
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login de usuário"""
    try:
        # Import here to avoid circular imports
        from src.app import db, Usuario
        
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username e password são obrigatórios'
            }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Buscar usuário
        user = Usuario.query.filter_by(username=username, ativo=True).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({
                'success': False,
                'message': 'Credenciais inválidas'
            }), 401
        
        # Atualizar último login
        user.ultimo_login = datetime.utcnow()
        db.session.commit()
        
        # Criar sessão
        session['user_id'] = user.id
        session['username'] = user.username
        session['perfil'] = user.perfil
        
        logger.info(f"Successful login for user: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Login realizado com sucesso',
            'user': {
                'id': user.id,
                'username': user.username,
                'perfil': user.perfil
            }
        })
        
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout de usuário"""
    try:
        username = session.get('username', 'unknown')
        session.clear()
        
        logger.info(f"User logged out: {username}")
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Error in logout: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500

@auth_bp.route('/check', methods=['GET'])
def check():
    """Verificar se usuário está autenticado"""
    try:
        from src.app import Usuario
        
        if 'user_id' not in session:
            return jsonify({
                'authenticated': False,
                'message': 'Usuário não autenticado'
            }), 401
        
        user = Usuario.query.get(session['user_id'])
        if not user or not user.ativo:
            session.clear()
            return jsonify({
                'authenticated': False,
                'message': 'Usuário inválido ou inativo'
            }), 401
        
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'perfil': user.perfil
            }
        })
        
    except Exception as e:
        logger.error(f"Error in auth check: {e}")
        return jsonify({
            'authenticated': False,
            'message': 'Erro interno do servidor'
        }), 500
