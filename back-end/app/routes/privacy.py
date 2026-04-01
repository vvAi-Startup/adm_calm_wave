from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
from app.services.cloudinary_service import delete_asset

privacy_bp = Blueprint('privacy', __name__)


@privacy_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    current_user_id = get_jwt_identity()
    user_resp = supabase.table('users').select('*').eq('id', current_user_id).execute()
    if not user_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = user_resp.data[0]
    user.pop('password_hash', None)

    data = {
        "profile": user,
        "devices": supabase.table('user_devices').select('*').eq('user_id', current_user_id).execute().data or [],
        "settings": supabase.table('settings').select('*').eq('user_id', current_user_id).execute().data or [],
        "achievements": supabase.table('user_achievements').select('*').eq('user_id', current_user_id).execute().data or [],
        "playlists": supabase.table('playlists').select('*').eq('user_id', current_user_id).execute().data or [],
        "audios_metadata": supabase.table('audios').select('*').eq('user_id', current_user_id).execute().data or [],
        "events_log": supabase.table('events').select('*').eq('user_id', current_user_id).execute().data or [],
        "statistics": supabase.table('statistics').select('*').eq('user_id', current_user_id).execute().data or [],
        "support_tickets": supabase.table('support_tickets').select('*').eq('user_id', current_user_id).execute().data or [],
    }
    return jsonify({"message": "Dados exportados", "data": data})


@privacy_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    current_user_id = get_jwt_identity()
    user_resp = supabase.table('users').select('id').eq('id', current_user_id).execute()
    if not user_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404

    # Delete physical/remote audio files
    audios = supabase.table('audios').select('file_path,processed_path').eq('user_id', current_user_id).execute().data or []
    for audio in audios:
        for path_key in ['file_path', 'processed_path']:
            p = audio.get(path_key)
            delete_asset(p)

    # Delete related records
    for table in ['audios', 'user_devices', 'user_achievements', 'settings',
                  'notifications', 'events', 'statistics', 'playlists', 'support_tickets']:
        supabase.table(table).delete().eq('user_id', current_user_id).execute()

    supabase.table('users').delete().eq('id', current_user_id).execute()
    return jsonify({"message": "Sua conta e todos os dados vinculados foram excluidos permanentemente."})
