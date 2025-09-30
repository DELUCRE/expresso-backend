"""
Main API routes
"""

from flask import Blueprint, request, jsonify, session
import logging
import random
import string

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

def require_auth():
    """Check if user is authenticated"""
    if 'user_id' not in session:
        return False
    return True

@api_bp.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Get dashboard statistics"""
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        from src.app import Entrega
        
        total_entregas = Entrega.query.count()
        pendentes = Entrega.query.filter_by(status='pendente').count()
        em_transito = Entrega.query.filter_by(status='em_transito').count()
        entregues = Entrega.query.filter_by(status='entregue').count()
        
        return jsonify({
            'total': total_entregas,
            'pendentes': pendentes,
            'em_transito': em_transito,
            'entregues': entregues
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/entregas', methods=['GET'])
def listar_entregas():
    """List all deliveries"""
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        from src.app import Entrega
        
        entregas = Entrega.query.order_by(Entrega.data_criacao.desc()).all()
        return jsonify([entrega.to_dict() for entrega in entregas])
        
    except Exception as e:
        logger.error(f"List deliveries error: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/entregas', methods=['POST'])
def criar_entrega():
    """Create new delivery"""
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Generate tracking code
        codigo = 'EI' + ''.join(random.choices(string.digits, k=8))
        
        from src.app import Entrega, db
        
        nova_entrega = Entrega(
            codigo_rastreamento=codigo,
            remetente_nome=data.get('remetente_nome'),
            remetente_endereco=data.get('remetente_endereco'),
            remetente_cidade=data.get('remetente_cidade'),
            remetente_telefone=data.get('remetente_telefone'),
            destinatario_nome=data.get('destinatario_nome'),
            destinatario_endereco=data.get('destinatario_endereco'),
            destinatario_cidade=data.get('destinatario_cidade'),
            destinatario_telefone=data.get('destinatario_telefone'),
            tipo_produto=data.get('tipo_produto'),
            peso=data.get('peso'),
            valor_declarado=data.get('valor_declarado'),
            observacoes=data.get('observacoes'),
            usuario_id=session['user_id']
        )
        
        db.session.add(nova_entrega)
        db.session.commit()
        
        logger.info(f"New delivery created: {codigo}")
        
        return jsonify({
            'success': True,
            'message': 'Entrega criada com sucesso',
            'codigo_rastreamento': codigo
        })
        
    except Exception as e:
        logger.error(f"Create delivery error: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/entregas/<int:entrega_id>', methods=['PUT'])
def atualizar_entrega(entrega_id):
    """Update delivery"""
    if not require_auth():
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        from src.app import Entrega, db
        
        entrega = Entrega.query.get_or_404(entrega_id)
        data = request.get_json()
        
        if 'status' in data:
            entrega.status = data['status']
        if 'observacoes' in data:
            entrega.observacoes = data['observacoes']
        
        db.session.commit()
        
        logger.info(f"Delivery updated: {entrega.codigo_rastreamento}")
        
        return jsonify({
            'success': True,
            'message': 'Entrega atualizada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Update delivery error: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/rastreamento/<codigo>', methods=['GET'])
def rastreamento(codigo):
    """Public tracking endpoint"""
    try:
        from src.app import Entrega
        
        entrega = Entrega.query.filter_by(codigo_rastreamento=codigo).first()
        
        if not entrega:
            return jsonify({'error': 'Código de rastreamento não encontrado'}), 404
        
        return jsonify({
            'codigo_rastreamento': entrega.codigo_rastreamento,
            'status': entrega.status,
            'remetente_cidade': entrega.remetente_cidade,
            'destinatario_cidade': entrega.destinatario_cidade,
            'data_criacao': entrega.data_criacao.isoformat() if entrega.data_criacao else None,
            'data_atualizacao': entrega.data_atualizacao.isoformat() if entrega.data_atualizacao else None
        })
        
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/contato', methods=['POST'])
def contato():
    """Contact form endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        nome = data.get('nome')
        email = data.get('email')
        assunto = data.get('assunto')
        mensagem = data.get('mensagem')
        
        # Log contact message
        logger.info(f"Contact message from {nome} ({email}): {assunto}")
        
        # Here you would typically send an email or save to database
        
        return jsonify({
            'success': True,
            'message': 'Mensagem enviada com sucesso! Entraremos em contato em breve.'
        })
        
    except Exception as e:
        logger.error(f"Contact error: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao enviar mensagem. Tente novamente.'
        }), 500
