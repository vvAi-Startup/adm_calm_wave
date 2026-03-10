from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
import json

users_bp = Blueprint("users", __name__)


def _user_to_dict(u):
    return {
        "id": u["id"],
        "email": u["email"],
        "name": u["name"],
        "profile_photo_url": u.get("profile_photo_url"),
        "created_at": u.get("created_at"),
        "last_access": u.get("last_access"),
        "active": u.get("active", True),
        "account_type": u.get("account_type", "free"),
        "role": u.get("role", "user"),
        "settings": {
            "dark_mode": u.get("dark_mode", False),
            "notifications_enabled": u.get("notifications_enabled", True),
            "auto_process_audio": u.get("auto_process_audio", True),
            "audio_quality": u.get("audio_quality", "high"),
        },
    }


@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    offset = (page - 1) * per_page

    q = supabase.table('users').select('*', count='exact').order('created_at', desc=True)
    if search:
        q = q.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0

    return jsonify({
        "users": [_user_to_dict(u) for u in (resp.data or [])],
        "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    })


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    resp = supabase.table('users').select('*').eq('id', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    return jsonify({"user": _user_to_dict(resp.data[0])})


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('users').select('*').eq('id', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}

    for field in ['name', 'active', 'account_type']:
        if field in data and user.get(field) != data[field]:
            changes[field] = {"old": user.get(field), "new": data[field]}
            update_data[field] = data[field]
    if "profile_photo_url" in data:
        update_data["profile_photo_url"] = data["profile_photo_url"]

    if update_data:
        supabase.table('users').update(update_data).eq('id', user_id).execute()
    if changes:
        supabase.table('events').insert({
            "user_id": current_user_id,
            "event_type": "USER_UPDATED",
            "level": "info",
            "screen": "users",
            "details_json": json.dumps({"target_user_id": user_id, "changes": changes}),
        }).execute()

    updated = supabase.table('users').select('*').eq('id', user_id).execute().data[0]
    return jsonify({"user": _user_to_dict(updated)})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('users').select('email').eq('id', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    email = resp.data[0]['email']
    supabase.table('users').update({"active": False}).eq('id', user_id).execute()
    supabase.table('events').insert({
        "user_id": current_user_id,
        "event_type": "USER_DEACTIVATED",
        "level": "warn",
        "screen": "users",
        "details_json": json.dumps({"target_user_id": user_id, "email": email}),
    }).execute()
    return jsonify({"message": "Usuario desativado com sucesso"})


@users_bp.route("/me/settings", methods=["PUT"])
@jwt_required()
def update_my_settings():
    current_user_id = get_jwt_identity()
    resp = supabase.table('users').select('*').eq('id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    data = request.get_json()
    update_data = {k: data[k] for k in ['dark_mode', 'notifications_enabled', 'auto_process_audio', 'audio_quality', 'name'] if k in data}
    if update_data:
        supabase.table('users').update(update_data).eq('id', current_user_id).execute()
    updated = supabase.table('users').select('*').eq('id', current_user_id).execute().data[0]
    return jsonify({"user": _user_to_dict(updated)})


@users_bp.route("/me/devices", methods=["GET"])
@jwt_required()
def get_my_devices():
    current_user_id = get_jwt_identity()
    resp = supabase.table('user_devices').select('*').eq('user_id', current_user_id).order('last_active', desc=True).execute()
    devices = resp.data or []
    if not devices:
        new_device = {
            "user_id": current_user_id,
            "device_name": request.headers.get("User-Agent", "Navegador Web")[:255],
            "device_type": "Desktop",
            "ip_address": request.remote_addr,
            "is_current": True,
        }
        created = supabase.table('user_devices').insert(new_device).execute()
        devices = created.data or []
    return jsonify({"devices": devices})


@users_bp.route("/me/devices/<int:device_id>", methods=["DELETE"])
@jwt_required()
def revoke_device(device_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('user_devices').select('id').eq('id', device_id).eq('user_id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Dispositivo nao encontrado"}), 404
    supabase.table('user_devices').delete().eq('id', device_id).execute()
    return jsonify({"success": True})


@users_bp.route("/me/devices/revoke_all", methods=["POST"])
@jwt_required()
def revoke_all_devices():
    current_user_id = get_jwt_identity()
    supabase.table('user_devices').delete().eq('user_id', current_user_id).eq('is_current', False).execute()
    return jsonify({"success": True})


@users_bp.route("/me/achievements", methods=["GET"])
@jwt_required()
def get_my_achievements():
    current_user_id = get_jwt_identity()
    audios_resp = supabase.table('audios').select('id,processed').eq('user_id', current_user_id).execute()
    all_audios = audios_resp.data or []
    total_audios = len(all_audios)
    processed_audios = sum(1 for a in all_audios if a.get('processed'))

    unlocked_resp = supabase.table('user_achievements').select('achievement_id').eq('user_id', current_user_id).execute()
    unlocked_ids = [a['achievement_id'] for a in (unlocked_resp.data or [])]

    achievements_metadata = [
        {"id": 1, "icon": "🎙️", "name": "Primeira Gravacao", "desc": "Gravou o primeiro audio no app"},
        {"id": 2, "icon": "🎖️", "name": "10 Gravacoes", "desc": "Gravou 10 audios"},
        {"id": 3, "icon": "🔥", "name": "7 Dias Seguidos", "desc": "Usou o app por 7 dias consecutivos"},
        {"id": 4, "icon": "🎵", "name": "50 Audios Limpos", "desc": "Processou 50 audios com IA"},
    ]
    results, new_unlocks = [], []
    for meta in achievements_metadata:
        earned = meta["id"] in unlocked_ids
        if not earned:
            if meta["id"] == 1 and total_audios >= 1:
                earned = True
            elif meta["id"] == 2 and total_audios >= 10:
                earned = True
            elif meta["id"] == 4 and processed_audios >= 50:
                earned = True
            if earned:
                new_unlocks.append({"user_id": current_user_id, "achievement_id": meta["id"]})
        count = total_audios if meta["id"] in [1, 2] else (processed_audios if meta["id"] == 4 else 1)
        results.append({"id": meta["id"], "icon": meta["icon"], "name": meta["name"], "desc": meta["desc"], "earned": earned, "count": count})

    if new_unlocks:
        supabase.table('user_achievements').insert(new_unlocks).execute()
    return jsonify({"achievements": results})
