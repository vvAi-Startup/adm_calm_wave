from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()
    try:
        # Notificações do usuário
        user_resp = supabase.table('notifications').select('*') \
            .eq('user_id', current_user_id).order('created_at', desc=True).limit(20).execute()
        # Notificações globais (user_id is null)
        global_resp = supabase.table('notifications').select('*') \
            .is_('user_id', None).order('created_at', desc=True).limit(20).execute()

        combined = (user_resp.data or []) + (global_resp.data or [])
        # Ordena por data desc e limita a 20
        combined.sort(key=lambda n: n.get('created_at', ''), reverse=True)
        return jsonify(combined[:20]), 200
    except Exception as e:
        return jsonify([]), 200  # retorna lista vazia em vez de 500



@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('notifications').select('*').eq('id', notification_id).execute()
    if not resp.data:
        return jsonify({"error": "Notificacao nao encontrada"}), 404
    n = resp.data[0]
    if n.get('user_id') is not None and str(n['user_id']) != str(current_user_id):
        return jsonify({"error": "Acesso nao autorizado"}), 403
    supabase.table('notifications').update({"is_read": True}).eq('id', notification_id).execute()
    updated = supabase.table('notifications').select('*').eq('id', notification_id).execute().data[0]
    return jsonify({"message": "Notificacao lida", "notification": updated}), 200


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    current_user_id = get_jwt_identity()
    supabase.table('notifications').update({"is_read": True}).or_(
        f'user_id.eq.{current_user_id},user_id.is.null'
    ).eq('is_read', False).execute()
    return jsonify({"message": "Todas as notificacoes lidas"}), 200


@notifications_bp.route('/broadcast', methods=['POST'])
@jwt_required()
def broadcast():
    """Admin: cria uma notificação global (user_id = null) visível a todos."""
    current_user_id = get_jwt_identity()

    # Verifica se é admin
    user_resp = supabase.table('users').select('role').eq('id', current_user_id).execute()
    if not user_resp.data or user_resp.data[0].get('role') != 'admin':
        return jsonify({"error": "Acesso restrito a administradores"}), 403

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    message = (data.get('message') or '').strip()
    n_type = data.get('type', 'info')

    if not title or not message:
        return jsonify({"error": "title e message são obrigatórios"}), 400

    if n_type not in ('info', 'success', 'warning', 'danger'):
        n_type = 'info'

    supabase.table('notifications').insert({
        'user_id': None,
        'title': title,
        'message': message,
        'type': n_type,
        'is_read': False,
    }).execute()

    return jsonify({"message": "Notificação global enviada com sucesso"}), 201

