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
