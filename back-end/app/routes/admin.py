from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
from datetime import datetime, timedelta
from collections import Counter
import bcrypt, json

admin_bp = Blueprint("admin", __name__)


def _get_role(user_id):
    resp = supabase.table('users').select('role,account_type').eq('id', user_id).execute()
    return resp.data[0] if resp.data else None

def is_admin(user_id):
    u = _get_role(user_id)
    return u and u.get('role') in ('admin', 'super_admin')

def is_super_admin(user_id):
    u = _get_role(user_id)
    return u and u.get('role') == 'super_admin'

def _safe_user(u):
    u.pop('password_hash', None)
    return u

def _count(table, **filters):
    q = supabase.table(table).select('*', count='exact')
    for k, v in filters.items():
        q = q.eq(k, v)
    return q.execute().count or 0


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def admin_list_users():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    acct = request.args.get("account_type", None)
    offset = (page - 1) * per_page
    q = supabase.table('users').select('*', count='exact').order('created_at', desc=True)
    if search:
        q = q.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    if acct:
        q = q.eq('account_type', acct)
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    return jsonify({
        "users": [_safe_user(u) for u in (resp.data or [])],
        "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    }), 200


@admin_bp.route("/users", methods=["POST"])
@jwt_required()
def admin_create_user():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    data = request.get_json()
    if not data or not all(k in data for k in ["name", "email", "password"]):
        return jsonify({"error": "Nome, email e senha sao obrigatorios"}), 400
    if supabase.table('users').select('id').eq('email', data['email']).execute().data:
        return jsonify({"error": "Email ja cadastrado"}), 409
    pw_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    resp = supabase.table('users').insert({
        "name": data["name"], "email": data["email"], "password_hash": pw_hash,
        "account_type": data.get("account_type", "free"), "role": data.get("role", "user"), "active": True,
    }).execute()
    user = _safe_user(resp.data[0])
    supabase.table('events').insert({
        "user_id": cid, "event_type": "ADMIN_USER_CREATED", "level": "info", "screen": "admin",
        "details_json": json.dumps({"target_user_id": user['id'], "email": user['email'], "account_type": user['account_type']}),
    }).execute()
    return jsonify({"user": user}), 201


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def admin_update_user(user_id):
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    resp = supabase.table('users').select('*').eq('id', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in ['name', 'account_type', 'active']:
        if field in data and user.get(field) != data[field]:
            changes[field] = {"old": user.get(field), "new": data[field]}
            update_data[field] = data[field]
    if "role" in data and user['role'] != data["role"]:
        if not is_super_admin(cid) and (data["role"] in ["admin","super_admin"] or user['role'] in ["admin","super_admin"]):
            return jsonify({"error": "Apenas Super Admins podem alterar papeis restritos."}), 403
        changes["role"] = {"old": user['role'], "new": data["role"]}
        update_data["role"] = data["role"]
    if update_data:
        supabase.table('users').update(update_data).eq('id', user_id).execute()
    if changes:
        supabase.table('events').insert({
            "user_id": cid, "event_type": "ADMIN_USER_UPDATED", "level": "info", "screen": "admin",
            "details_json": json.dumps({"target_user_id": user_id, "changes": changes}),
        }).execute()
    updated = _safe_user(supabase.table('users').select('*').eq('id', user_id).execute().data[0])
    return jsonify({"user": updated})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id):
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    if cid == user_id:
        return jsonify({"error": "Voce nao pode deletar sua propria conta"}), 400
    resp = supabase.table('users').select('email').eq('id', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    email = resp.data[0]['email']
    supabase.table('users').update({"active": False}).eq('id', user_id).execute()
    supabase.table('events').insert({
        "user_id": cid, "event_type": "ADMIN_USER_DELETED", "level": "warn", "screen": "admin",
        "details_json": json.dumps({"target_user_id": user_id, "email": email}),
    }).execute()
    return jsonify({"message": "Usuario deletado com sucesso"})


@admin_bp.route("/reports/overview", methods=["GET"])
@jwt_required()
def admin_report_overview():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    return jsonify({
        "users": {
            "total": _count('users'), "active": _count('users', active=True),
            "admins": _count('users', account_type='admin'), "premium": _count('users', account_type='premium'),
            "free": _count('users', account_type='free'),
        },
        "audios": {
            "total": _count('audios'), "processed": _count('audios', processed=True),
            "processed_pct": round((_count('audios', processed=True) / max(_count('audios'), 1)) * 100, 1),
            "transcribed": _count('audios', transcribed=True), "favorite": _count('audios', favorite=True),
        },
        "metrics": {
            "avg_audios_per_user": round(_count('audios') / max(_count('users', active=True), 1), 2),
            "total_events": _count('events'), "error_events": _count('events', level='error'),
        },
        "today": {
            "audios": supabase.table('audios').select('*', count='exact').gte('recorded_at', today).execute().count or 0,
            "registrations": supabase.table('users').select('*', count='exact').gte('created_at', today).execute().count or 0,
            "events": supabase.table('events').select('*', count='exact').gte('created_at', today).execute().count or 0,
        },
    })


@admin_bp.route("/reports/users", methods=["GET"])
@jwt_required()
def admin_report_users():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    daily_registrations = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        cnt = supabase.table('users').select('*', count='exact').gte('created_at', ds.isoformat()).lt('created_at', de.isoformat()).execute().count or 0
        daily_registrations.append({"day": day.strftime("%a"), "count": cnt})
    users_data = supabase.table('users').select('id,name,email').execute().data or []
    user_audio_counts = []
    for u in users_data:
        cnt = supabase.table('audios').select('*', count='exact').eq('user_id', u['id']).execute().count or 0
        user_audio_counts.append({"id": u['id'], "name": u['name'], "email": u['email'], "audio_count": cnt})
    top_users = sorted(user_audio_counts, key=lambda x: x['audio_count'], reverse=True)[:10]
    return jsonify({"daily_registrations": daily_registrations, "top_users": top_users})


@admin_bp.route("/reports/audios", methods=["GET"])
@jwt_required()
def admin_report_audios():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    daily_uploads = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        ds = day.replace(hour=0, minute=0, second=0, microsecond=0)
        de = ds + timedelta(days=1)
        cnt = supabase.table('audios').select('*', count='exact').gte('recorded_at', ds.isoformat()).lt('recorded_at', de.isoformat()).execute().count or 0
        daily_uploads.append({"day": day.strftime("%a"), "count": cnt})
    processed_data = supabase.table('audios').select('processing_time_ms').eq('processed', True).execute().data or []
    total_pt = sum((a.get('processing_time_ms') or 0) for a in processed_data)
    pc = len(processed_data)
    all_audios = supabase.table('audios').select('size_bytes').execute().data or []
    total_size = sum((a.get('size_bytes') or 0) for a in all_audios)
    return jsonify({
        "daily_uploads": daily_uploads,
        "processing": {"total_processed": pc, "total_processing_time_ms": int(total_pt), "avg_processing_time_ms": round(total_pt / pc, 2) if pc > 0 else 0},
        "storage": {"total_bytes": total_size, "total_mb": round(total_size/(1024*1024), 2), "total_gb": round(total_size/(1024**3), 2)},
    })


@admin_bp.route("/reports/events", methods=["GET"])
@jwt_required()
def admin_report_events():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    level = request.args.get("level", None)
    event_type = request.args.get("event_type", None)
    offset = (page - 1) * per_page
    q = supabase.table('events').select('*', count='exact').order('created_at', desc=True)
    if level:
        q = q.eq('level', level)
    if event_type:
        q = q.eq('event_type', event_type)
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    all_ev = supabase.table('events').select('event_type').execute().data or []
    dist = Counter(e['event_type'] for e in all_ev).most_common(10)
    return jsonify({
        "events": resp.data or [], "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
        "distribution": [{"event_type": k, "count": v} for k, v in dist],
    })


@admin_bp.route("/notifications/broadcast", methods=["POST"])
@jwt_required()
def admin_broadcast_notification():
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    data = request.get_json()
    if not data or not all(k in data for k in ["title", "message"]):
        return jsonify({"error": "Titulo e mensagem sao obrigatorios"}), 400
    notif = supabase.table('notifications').insert({
        "user_id": None, "title": data["title"], "message": data["message"],
        "type": data.get("type", "info"), "is_read": False,
    }).execute()
    supabase.table('events').insert({
        "user_id": cid, "event_type": "ADMIN_BROADCAST", "level": "info", "screen": "admin",
        "details_json": json.dumps({"title": data["title"], "message": data["message"]}),
    }).execute()
    return jsonify({"notification": notif.data[0]}), 201


@admin_bp.route("/notifications/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_notification(notification_id):
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    if not supabase.table('notifications').select('id').eq('id', notification_id).execute().data:
        return jsonify({"error": "Notificacao nao encontrada"}), 404
    supabase.table('notifications').delete().eq('id', notification_id).execute()
    return jsonify({"message": "Notificacao deletada com sucesso"})


@admin_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def admin_audit_logs():
    cid = get_jwt_identity()
    if not is_super_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas super administradores."}), 403
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page
    resp = supabase.table('events').select('*', count='exact').like('event_type', 'ADMIN_%').order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    return jsonify({
        "logs": resp.data or [], "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    })
