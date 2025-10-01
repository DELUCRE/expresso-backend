"""
Main API routes
"""

import logging
import random
import string
from datetime import datetime
from flask import Blueprint, request, jsonify, session

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

def require_auth(f):
    """Decorator para rotas que requerem autenticação"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Autenticação necessária'
            }), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def generate_tracking_code():
    """Gerar código de rastreamento único"""
    prefix = "EXP"
    suffix = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{suffix}"

@api_bp.route('/entregas', methods=['GET'])
@require_auth
def get_entregas():
    """Listar entregas"""
    try:
        from src.app import Entrega
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status_filter = request.args.get('status')
        
        query = Entrega.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        entregas = query.order_by(Entrega.data_criacao.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'entregas': [entrega.to_dict() for entrega in entregas.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': entregas.total,
                'pages': entregas.pages
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting entregas: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar entregas'
        }), 500

@api_bp.route('/entregas', methods=['POST'])
@require_auth
def create_entrega():
    """Criar nova entrega"""
    try:
        from src.app import db, Entrega
        
        data = request.get_json()
        
        # Validação básica
        required_fields = [
            'remetente_nome', 'remetente_endereco', 'remetente_cidade',
            'destinatario_nome', 'destinatario_endereco', 'destinatario_cidade',
            'tipo_produto'
        ]
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório: {field}'
                }), 400
        
        # Criar entrega
        entrega = Entrega(
            codigo_rastreamento=generate_tracking_code(),
            remetente_nome=data['remetente_nome'],
            remetente_endereco=data['remetente_endereco'],
            remetente_cidade=data['remetente_cidade'],
            remetente_telefone=data.get('remetente_telefone'),
            destinatario_nome=data['destinatario_nome'],
            destinatario_endereco=data['destinatario_endereco'],
            destinatario_cidade=data['destinatario_cidade'],
            destinatario_telefone=data.get('destinatario_telefone'),
            tipo_produto=data['tipo_produto'],
            peso=data.get('peso'),
            valor_declarado=data.get('valor_declarado'),
            observacoes=data.get('observacoes'),
            usuario_id=session['user_id']
        )
        
        db.session.add(entrega)
        db.session.commit()
        
        logger.info(f"New entrega created: {entrega.codigo_rastreamento}")
        
        return jsonify({
            'success': True,
            'message': 'Entrega criada com sucesso',
            'entrega': entrega.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating entrega: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar entrega'
        }), 500

@api_bp.route('/contato', methods=['POST'])
def contato():
    """Endpoint para formulário de contato (público)"""
    try:
        data = request.get_json()
        
        required_fields = ['nome', 'email', 'mensagem']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório: {field}'
                }), 400
        
        # Log da mensagem de contato
        logger.info(f"Contact form submission from {data['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Mensagem enviada com sucesso! Entraremos em contato em breve.'
        })
        
    except Exception as e:
        logger.error(f"Error processing contact form: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao enviar mensagem. Tente novamente.'
        }), 500
