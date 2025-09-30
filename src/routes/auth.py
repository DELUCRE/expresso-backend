"""
Authentication routes
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
        
        from src.app import Usuario
        usuario = Usuario.query.filter_by(username=username, ativo=True).first()
        
        if usuario and usuario.check_password(password):
            # Update last login
            usuario.ultimo_login = datetime.utcnow()
            from src.app import db
            db.session.commit()
            
            # Set session
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['perfil'] = usuario.perfil
            session.permanent = True
            
            logger.info(f"Login successful for user: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'user': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'perfil': usuario.perfil
                }
            })
        else:
            logger.warning(f"Login failed for user: {username}")
            return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@auth_bp.route('/check', methods=['GET'])
def check():
    """Check authentication status"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'perfil': session['perfil']
            }
        })
    else:
        return jsonify({'authenticated': False}), 401
