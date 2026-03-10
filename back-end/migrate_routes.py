"""Script to migrate all route files from SQLAlchemy to Supabase REST API."""
import os

BASE = os.path.join(os.path.dirname(__file__), 'app', 'routes')
SVC  = os.path.join(os.path.dirname(__file__), 'app', 'services')

files = {}

# ── push_service.py ──────────────────────────────────────────────────────────
files[os.path.join(SVC, 'push_service.py')] = '''\
import json
from app.supabase_ext import supabase


class PushService:
    @staticmethod
    def send_push_notification(user_id, title, message, data_payload=None):
        """
        Simula envio de notificacao Push e salva no Supabase.
        """
        try:
            supabase.table('notifications').insert({
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": "PUSH",
                "is_read": False,
            }).execute()
        except Exception as e:
            print(f"[PUSH] Erro ao salvar notificacao: {e}")

        print(f"[PUSH MOCK] Enviando para User {user_id}: {title} - {message}")
        if data_payload:
            print(f"[PUSH MOCK] Payload: {json.dumps(data_payload)}")
        return True
'''

# ── events.py ─────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'events.py')] = '''\
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.supabase_ext import supabase
import json

events_bp = Blueprint("events", __name__)


@events_bp.route("/", methods=["GET"])
@jwt_required()
def list_events():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    level = request.args.get("level", None)
    offset = (page - 1) * per_page

    query = supabase.table(\'events\').select(\'*\', count=\'exact\').order(\'created_at\', desc=True)
    if level:
        query = query.eq(\'level\', level)
    resp = query.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return jsonify({
        "events": resp.data or [],
        "total": total,
        "pages": pages,
    })


@events_bp.route("/", methods=["POST"])
@jwt_required()
def create_event():
    data = request.get_json()
    event = {
        "user_id": data.get("user_id"),
        "event_type": data.get("event_type", "unknown"),
        "details_json": json.dumps(data.get("details", {})),
        "screen": data.get("screen"),
        "level": data.get("level", "info"),
    }
    resp = supabase.table(\'events\').insert(event).execute()
    return jsonify({"event": resp.data[0]}), 201
'''

# ── notifications.py ──────────────────────────────────────────────────────────
files[os.path.join(BASE, 'notifications.py')] = '''\
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase

notifications_bp = Blueprint(\'notifications\', __name__)


@notifications_bp.route(\'/\', methods=[\'GET\'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'notifications\').select(\'*\').or_(
        f\'user_id.eq.{current_user_id},user_id.is.null\'
    ).order(\'created_at\', desc=True).limit(20).execute()
    return jsonify(resp.data or []), 200


@notifications_bp.route(\'/<int:notification_id>/read\', methods=[\'PUT\'])
@jwt_required()
def mark_read(notification_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'notifications\').select(\'*\').eq(\'id\', notification_id).execute()
    if not resp.data:
        return jsonify({"error": "Notificacao nao encontrada"}), 404
    n = resp.data[0]
    if n.get(\'user_id\') is not None and str(n[\'user_id\']) != str(current_user_id):
        return jsonify({"error": "Acesso nao autorizado"}), 403
    supabase.table(\'notifications\').update({"is_read": True}).eq(\'id\', notification_id).execute()
    updated = supabase.table(\'notifications\').select(\'*\').eq(\'id\', notification_id).execute().data[0]
    return jsonify({"message": "Notificacao lida", "notification": updated}), 200


@notifications_bp.route(\'/read-all\', methods=[\'PUT\'])
@jwt_required()
def mark_all_read():
    current_user_id = get_jwt_identity()
    supabase.table(\'notifications\').update({"is_read": True}).or_(
        f\'user_id.eq.{current_user_id},user_id.is.null\'
    ).eq(\'is_read\', False).execute()
    return jsonify({"message": "Todas as notificacoes lidas"}), 200
'''

# ── billing.py ────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'billing.py')] = '''\
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase

billing_bp = Blueprint(\'billing\', __name__)


@billing_bp.route(\'/plan\', methods=[\'GET\'])
@jwt_required()
def get_plan_details():
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'users\').select(\'account_type\').eq(\'id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    account_type = resp.data[0][\'account_type\']

    if account_type == "premium":
        limits = {
            "max_audio_length_seconds": 3600,
            "max_storage_mb": 5000,
            "transcription_included": True,
        }
    else:
        limits = {
            "max_audio_length_seconds": 300,
            "max_storage_mb": 100,
            "transcription_included": False,
        }
    return jsonify({"account_type": account_type, "limits": limits})


@billing_bp.route(\'/upgrade\', methods=[\'POST\'])
@jwt_required()
def upgrade_plan():
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'users\').select(\'id\').eq(\'id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    data = request.get_json() or {}
    desired_plan = data.get("plan", "premium")
    if desired_plan not in ["free", "premium"]:
        return jsonify({"error": "Plano invalido."}), 400
    supabase.table(\'users\').update({"account_type": desired_plan}).eq(\'id\', current_user_id).execute()
    return jsonify({
        "message": f"Assinatura alterada para {desired_plan} com sucesso",
        "account_type": desired_plan,
    })
'''

# ── privacy.py ────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'privacy.py')] = '''\
from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
import os

privacy_bp = Blueprint(\'privacy\', __name__)


@privacy_bp.route(\'/export\', methods=[\'GET\'])
@jwt_required()
def export_data():
    current_user_id = get_jwt_identity()
    user_resp = supabase.table(\'users\').select(\'*\').eq(\'id\', current_user_id).execute()
    if not user_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = user_resp.data[0]
    user.pop(\'password_hash\', None)

    data = {
        "profile": user,
        "devices": supabase.table(\'user_devices\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "settings": supabase.table(\'settings\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "achievements": supabase.table(\'user_achievements\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "playlists": supabase.table(\'playlists\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "audios_metadata": supabase.table(\'audios\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "events_log": supabase.table(\'events\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "statistics": supabase.table(\'statistics\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
        "support_tickets": supabase.table(\'support_tickets\').select(\'*\').eq(\'user_id\', current_user_id).execute().data or [],
    }
    return jsonify({"message": "Dados exportados", "data": data})


@privacy_bp.route(\'/delete-account\', methods=[\'DELETE\'])
@jwt_required()
def delete_account():
    current_user_id = get_jwt_identity()
    user_resp = supabase.table(\'users\').select(\'id\').eq(\'id\', current_user_id).execute()
    if not user_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404

    # Delete physical audio files
    audios = supabase.table(\'audios\').select(\'file_path,processed_path\').eq(\'user_id\', current_user_id).execute().data or []
    for audio in audios:
        for path_key in [\'file_path\', \'processed_path\']:
            p = audio.get(path_key)
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    # Delete related records
    for table in [\'audios\', \'user_devices\', \'user_achievements\', \'settings\',
                  \'notifications\', \'events\', \'statistics\', \'playlists\', \'support_tickets\']:
        supabase.table(table).delete().eq(\'user_id\', current_user_id).execute()

    supabase.table(\'users\').delete().eq(\'id\', current_user_id).execute()
    return jsonify({"message": "Sua conta e todos os dados vinculados foram excluidos permanentemente."})
'''

# ── playlists.py ──────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'playlists.py')] = '''\
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
import json

playlists_bp = Blueprint("playlists", __name__)


def _playlist_with_count(p):
    count = supabase.table(\'audios\').select(\'id\', count=\'exact\').eq(\'playlist_id\', p[\'id\']).execute().count or 0
    p[\'total_audios\'] = count
    return p


@playlists_bp.route("/", methods=["GET"])
@jwt_required()
def list_playlists():
    current_user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page

    resp = supabase.table(\'playlists\').select(\'*\', count=\'exact\').eq(\'user_id\', current_user_id).order(\'order\', desc=False).range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    playlists = [_playlist_with_count(p) for p in (resp.data or [])]

    return jsonify({
        "playlists": playlists,
        "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    })


@playlists_bp.route("/", methods=["POST"])
@jwt_required()
def create_playlist():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Nome da playlist e obrigatorio"}), 400

    last = supabase.table(\'playlists\').select(\'order\').eq(\'user_id\', current_user_id).order(\'order\', desc=True).limit(1).execute()
    next_order = (last.data[0][\'order\'] + 1) if last.data else 0

    resp = supabase.table(\'playlists\').insert({
        "user_id": current_user_id,
        "name": data["name"],
        "color": data.get("color", "#6FAF9E"),
        "order": next_order,
    }).execute()
    playlist = _playlist_with_count(resp.data[0])

    supabase.table(\'events\').insert({
        "user_id": current_user_id,
        "event_type": "PLAYLIST_CREATED",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"playlist_name": data["name"]}),
    }).execute()
    return jsonify({"playlist": playlist}), 201


@playlists_bp.route("/<int:playlist_id>", methods=["GET"])
@jwt_required()
def get_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'playlists\').select(\'*\').eq(\'id\', playlist_id).eq(\'user_id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    playlist = _playlist_with_count(resp.data[0])
    playlist["audios"] = supabase.table(\'audios\').select(\'*\').eq(\'playlist_id\', playlist_id).execute().data or []
    return jsonify({"playlist": playlist})


@playlists_bp.route("/<int:playlist_id>", methods=["PUT"])
@jwt_required()
def update_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'playlists\').select(\'*\').eq(\'id\', playlist_id).eq(\'user_id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    old = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in [\'name\', \'color\', \'order\']:
        if field in data and old.get(field) != data[field]:
            changes[field] = {"old": old.get(field), "new": data[field]}
            update_data[field] = data[field]
    if update_data:
        supabase.table(\'playlists\').update(update_data).eq(\'id\', playlist_id).execute()
    if changes:
        supabase.table(\'events\').insert({
            "user_id": current_user_id,
            "event_type": "PLAYLIST_UPDATED",
            "level": "info",
            "screen": "playlists",
            "details_json": json.dumps({"playlist_id": playlist_id, "changes": changes}),
        }).execute()
    updated = supabase.table(\'playlists\').select(\'*\').eq(\'id\', playlist_id).execute().data[0]
    return jsonify({"playlist": _playlist_with_count(updated)})


@playlists_bp.route("/<int:playlist_id>", methods=["DELETE"])
@jwt_required()
def delete_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'playlists\').select(\'*\').eq(\'id\', playlist_id).eq(\'user_id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    name = resp.data[0][\'name\']
    supabase.table(\'audios\').update({"playlist_id": None}).eq(\'playlist_id\', playlist_id).execute()
    supabase.table(\'playlists\').delete().eq(\'id\', playlist_id).execute()
    supabase.table(\'events\').insert({
        "user_id": current_user_id,
        "event_type": "PLAYLIST_DELETED",
        "level": "warn",
        "screen": "playlists",
        "details_json": json.dumps({"playlist_id": playlist_id, "name": name}),
    }).execute()
    return jsonify({"message": "Playlist removida com sucesso"})


@playlists_bp.route("/<int:playlist_id>/add-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def add_audio_to_playlist(playlist_id, audio_id):
    current_user_id = get_jwt_identity()
    if not supabase.table(\'playlists\').select(\'id\').eq(\'id\', playlist_id).eq(\'user_id\', current_user_id).execute().data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    a_resp = supabase.table(\'audios\').select(\'*\').eq(\'id\', audio_id).eq(\'user_id\', current_user_id).execute()
    if not a_resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = a_resp.data[0]
    if audio.get(\'playlist_id\') == playlist_id:
        return jsonify({"error": "Audio ja esta nesta playlist"}), 400
    old_playlist_id = audio.get(\'playlist_id\')
    supabase.table(\'audios\').update({"playlist_id": playlist_id}).eq(\'id\', audio_id).execute()
    supabase.table(\'events\').insert({
        "user_id": current_user_id,
        "event_type": "AUDIO_ADDED_TO_PLAYLIST",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"audio_id": audio_id, "playlist_id": playlist_id, "old_playlist_id": old_playlist_id}),
    }).execute()
    updated = supabase.table(\'audios\').select(\'*\').eq(\'id\', audio_id).execute().data[0]
    return jsonify({"audio": updated})


@playlists_bp.route("/<int:playlist_id>/remove-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def remove_audio_from_playlist(playlist_id, audio_id):
    current_user_id = get_jwt_identity()
    if not supabase.table(\'playlists\').select(\'id\').eq(\'id\', playlist_id).eq(\'user_id\', current_user_id).execute().data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    if not supabase.table(\'audios\').select(\'id\').eq(\'id\', audio_id).eq(\'user_id\', current_user_id).eq(\'playlist_id\', playlist_id).execute().data:
        return jsonify({"error": "Audio nao encontrado nesta playlist"}), 404
    supabase.table(\'audios\').update({"playlist_id": None}).eq(\'id\', audio_id).execute()
    supabase.table(\'events\').insert({
        "user_id": current_user_id,
        "event_type": "AUDIO_REMOVED_FROM_PLAYLIST",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"audio_id": audio_id, "playlist_id": playlist_id}),
    }).execute()
    return jsonify({"message": "Audio removido da playlist"})


@playlists_bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_playlists():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or not isinstance(data.get("playlists"), list):
        return jsonify({"error": "Formato invalido. \'playlists\' deve ser uma lista"}), 400
    created_count = updated_count = 0
    for p_data in data["playlists"]:
        name = p_data.get("name")
        if not name:
            continue
        color, order = p_data.get("color", "#6FAF9E"), p_data.get("order", 0)
        existing = supabase.table(\'playlists\').select(\'id\').eq(\'user_id\', current_user_id).eq(\'name\', name).execute()
        if existing.data:
            supabase.table(\'playlists\').update({"color": color, "order": order}).eq(\'id\', existing.data[0][\'id\']).execute()
            updated_count += 1
        else:
            supabase.table(\'playlists\').insert({"user_id": current_user_id, "name": name, "color": color, "order": order}).execute()
            created_count += 1
    return jsonify({"message": "Sincronizacao concluida", "created": created_count, "updated": updated_count}), 200
'''

# ── support.py ────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'support.py')] = '''\
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
from app.services.push_service import PushService

support_bp = Blueprint("support", __name__)


def _is_admin_user(user):
    return user.get(\'account_type\') == \'admin\' or user.get(\'role\') in (\'admin\', \'super_admin\')


def _ticket_with_count(t):
    count = supabase.table(\'ticket_messages\').select(\'id\', count=\'exact\').eq(\'ticket_id\', t[\'id\']).execute().count or 0
    t[\'messages_count\'] = count
    return t


@support_bp.route("/", methods=["GET"])
@jwt_required()
def list_tickets():
    current_user_id = get_jwt_identity()
    u_resp = supabase.table(\'users\').select(\'account_type,role\').eq(\'id\', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    if _is_admin_user(user):
        tickets = supabase.table(\'support_tickets\').select(\'*\').order(\'updated_at\', desc=True).execute().data or []
    else:
        tickets = supabase.table(\'support_tickets\').select(\'*\').eq(\'user_id\', current_user_id).order(\'updated_at\', desc=True).execute().data or []

    results = []
    for t in tickets:
        t = _ticket_with_count(t)
        eu = supabase.table(\'users\').select(\'email\').eq(\'id\', t[\'user_id\']).execute()
        t[\'user_email\'] = eu.data[0][\'email\'] if eu.data else \'Desconhecido\'
        lm = supabase.table(\'ticket_messages\').select(\'message\').eq(\'ticket_id\', t[\'id\']).order(\'sent_at\', desc=True).limit(1).execute()
        t[\'last_message\'] = lm.data[0][\'message\'] if lm.data else \'Sem mensagens\'
        results.append(t)
    return jsonify({"tickets": results})


@support_bp.route("/", methods=["POST"])
@jwt_required()
def create_ticket():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    subject = data.get("subject", "Sem Assunto")
    message = data.get("message", "")

    resp = supabase.table(\'support_tickets\').insert({
        "user_id": current_user_id,
        "subject": subject,
        "status": "open",
    }).execute()
    ticket = _ticket_with_count(resp.data[0])

    if message:
        supabase.table(\'ticket_messages\').insert({
            "ticket_id": ticket[\'id\'],
            "sender": "user",
            "message": message,
        }).execute()
    return jsonify({"ticket": ticket}), 201


@support_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    u_resp = supabase.table(\'users\').select(\'account_type,role\').eq(\'id\', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    t_resp = supabase.table(\'support_tickets\').select(\'*\').eq(\'id\', ticket_id).execute()
    if not t_resp.data:
        return jsonify({"error": "Ticket nao encontrado"}), 404
    ticket = t_resp.data[0]

    if not _is_admin_user(user) and ticket[\'user_id\'] != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403

    messages = supabase.table(\'ticket_messages\').select(\'*\').eq(\'ticket_id\', ticket_id).order(\'sent_at\', desc=False).execute().data or []
    eu = supabase.table(\'users\').select(\'email\').eq(\'id\', ticket[\'user_id\']).execute()
    ticket[\'user_email\'] = eu.data[0][\'email\'] if eu.data else \'Desconhecido\'
    ticket[\'messages_list\'] = messages
    ticket = _ticket_with_count(ticket)
    return jsonify({"ticket": ticket})


@support_bp.route("/<int:ticket_id>/reply", methods=["POST"])
@jwt_required()
def reply_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    u_resp = supabase.table(\'users\').select(\'account_type,role\').eq(\'id\', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    t_resp = supabase.table(\'support_tickets\').select(\'*\').eq(\'id\', ticket_id).execute()
    if not t_resp.data:
        return jsonify({"error": "Ticket nao encontrado"}), 404
    ticket = t_resp.data[0]

    if not _is_admin_user(user) and ticket[\'user_id\'] != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    sender = "admin" if _is_admin_user(user) else "user"
    msg_resp = supabase.table(\'ticket_messages\').insert({
        "ticket_id": ticket_id,
        "sender": sender,
        "message": message,
    }).execute()
    new_status = "answered" if sender == "admin" else "open"
    supabase.table(\'support_tickets\').update({"status": new_status}).eq(\'id\', ticket_id).execute()

    if sender == "admin":
        PushService.send_push_notification(
            user_id=ticket[\'user_id\'],
            title=f"Atualizacao no Chamado #{ticket_id}",
            message=f"Suporte: {message[:50]}...",
            data_payload={"ticket_id": ticket_id},
        )
    return jsonify({"message": msg_resp.data[0]}), 201
'''

# ── users.py ──────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'users.py')] = '''\
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

    q = supabase.table(\'users\').select(\'*\', count=\'exact\').order(\'created_at\', desc=True)
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
    resp = supabase.table(\'users\').select(\'*\').eq(\'id\', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    return jsonify({"user": _user_to_dict(resp.data[0])})


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'users\').select(\'*\').eq(\'id\', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}

    for field in [\'name\', \'active\', \'account_type\']:
        if field in data and user.get(field) != data[field]:
            changes[field] = {"old": user.get(field), "new": data[field]}
            update_data[field] = data[field]
    if "profile_photo_url" in data:
        update_data["profile_photo_url"] = data["profile_photo_url"]

    if update_data:
        supabase.table(\'users\').update(update_data).eq(\'id\', user_id).execute()
    if changes:
        supabase.table(\'events\').insert({
            "user_id": current_user_id,
            "event_type": "USER_UPDATED",
            "level": "info",
            "screen": "users",
            "details_json": json.dumps({"target_user_id": user_id, "changes": changes}),
        }).execute()

    updated = supabase.table(\'users\').select(\'*\').eq(\'id\', user_id).execute().data[0]
    return jsonify({"user": _user_to_dict(updated)})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'users\').select(\'email\').eq(\'id\', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    email = resp.data[0][\'email\']
    supabase.table(\'users\').update({"active": False}).eq(\'id\', user_id).execute()
    supabase.table(\'events\').insert({
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
    resp = supabase.table(\'users\').select(\'*\').eq(\'id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    data = request.get_json()
    update_data = {k: data[k] for k in [\'dark_mode\', \'notifications_enabled\', \'auto_process_audio\', \'audio_quality\', \'name\'] if k in data}
    if update_data:
        supabase.table(\'users\').update(update_data).eq(\'id\', current_user_id).execute()
    updated = supabase.table(\'users\').select(\'*\').eq(\'id\', current_user_id).execute().data[0]
    return jsonify({"user": _user_to_dict(updated)})


@users_bp.route("/me/devices", methods=["GET"])
@jwt_required()
def get_my_devices():
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'user_devices\').select(\'*\').eq(\'user_id\', current_user_id).order(\'last_active\', desc=True).execute()
    devices = resp.data or []
    if not devices:
        new_device = {
            "user_id": current_user_id,
            "device_name": request.headers.get("User-Agent", "Navegador Web")[:255],
            "device_type": "Desktop",
            "ip_address": request.remote_addr,
            "is_current": True,
        }
        created = supabase.table(\'user_devices\').insert(new_device).execute()
        devices = created.data or []
    return jsonify({"devices": devices})


@users_bp.route("/me/devices/<int:device_id>", methods=["DELETE"])
@jwt_required()
def revoke_device(device_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'user_devices\').select(\'id\').eq(\'id\', device_id).eq(\'user_id\', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Dispositivo nao encontrado"}), 404
    supabase.table(\'user_devices\').delete().eq(\'id\', device_id).execute()
    return jsonify({"success": True})


@users_bp.route("/me/devices/revoke_all", methods=["POST"])
@jwt_required()
def revoke_all_devices():
    current_user_id = get_jwt_identity()
    supabase.table(\'user_devices\').delete().eq(\'user_id\', current_user_id).eq(\'is_current\', False).execute()
    return jsonify({"success": True})


@users_bp.route("/me/achievements", methods=["GET"])
@jwt_required()
def get_my_achievements():
    current_user_id = get_jwt_identity()
    audios_resp = supabase.table(\'audios\').select(\'id,processed\').eq(\'user_id\', current_user_id).execute()
    all_audios = audios_resp.data or []
    total_audios = len(all_audios)
    processed_audios = sum(1 for a in all_audios if a.get(\'processed\'))

    unlocked_resp = supabase.table(\'user_achievements\').select(\'achievement_id\').eq(\'user_id\', current_user_id).execute()
    unlocked_ids = [a[\'achievement_id\'] for a in (unlocked_resp.data or [])]

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
        supabase.table(\'user_achievements\').insert(new_unlocks).execute()
    return jsonify({"achievements": results})
'''

# ── audios.py ─────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'audios.py')] = '''\
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from app.supabase_ext import supabase
import os, time, io, zipfile, json
from werkzeug.utils import secure_filename
from app.services.push_service import PushService

audios_bp = Blueprint("audios", __name__)

try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None
    print("Warning: Audio processor not available")


@audios_bp.route("/play/<int:audio_id>", methods=["GET"])
def play_audio(audio_id):
    resp = supabase.table(\'audios\').select(\'file_path,processed_path,processed\').eq(\'id\', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = resp.data[0]
    audio_type = request.args.get("type", "processed")
    if audio_type == "original":
        file_path = audio.get(\'file_path\')
    else:
        file_path = audio.get(\'processed_path\') if audio.get(\'processed\') and audio.get(\'processed_path\') else audio.get(\'file_path\')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo de audio nao encontrado"}), 404
    response = send_file(file_path, mimetype="audio/wav", conditional=True)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@audios_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_audio():
    if \'file\' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files[\'file\']
    if file.filename == \'\':
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".aac")):
        return jsonify({"error": "Formato nao suportado."}), 400

    user_id = get_jwt_identity()
    upload_dir = os.path.join(current_app.root_path, \'..\', \'uploads\')
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    audio_resp = supabase.table(\'audios\').insert({
        "user_id": user_id,
        "filename": filename,
        "file_path": file_path,
        "size_bytes": os.path.getsize(file_path),
        "device_origin": request.form.get("device_origin", "Web"),
        "processed": False,
        "transcribed": False,
        "favorite": False,
    }).execute()
    audio = audio_resp.data[0]

    supabase.table(\'events\').insert({
        "user_id": user_id, "event_type": "AUDIO_UPLOADED", "level": "info",
        "screen": "audio", "details_json": json.dumps({"filename": filename, "size": audio[\'size_bytes\']}),
    }).execute()

    if denoiser and denoiser.model is not None:
        try:
            start_time = time.time()
            with open(file_path, \'rb\') as f:
                audio_bytes = f.read()
            processed_bytes = denoiser.denoise_audio(audio_bytes)
            processed_filename = f"processed_{filename}"
            processed_path = os.path.join(upload_dir, processed_filename)
            with open(processed_path, \'wb\') as f:
                f.write(processed_bytes)
            update_data = {
                "processed": True,
                "processed_path": processed_path,
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }
            if transcribe_audio:
                u_resp = supabase.table(\'users\').select(\'transcription_language\').eq(\'id\', user_id).execute()
                lang = u_resp.data[0].get(\'transcription_language\', \'pt-BR\') if u_resp.data else \'pt-BR\'
                transcription = transcribe_audio(processed_path, language=lang)
                if transcription:
                    update_data["transcribed"] = True
                    update_data["transcription_text"] = transcription
            supabase.table(\'audios\').update(update_data).eq(\'id\', audio[\'id\']).execute()
            audio.update(update_data)
            supabase.table(\'events\').insert({
                "user_id": user_id, "event_type": "AUDIO_PROCESSED", "level": "info",
                "screen": "audio", "details_json": json.dumps({
                    "audio_id": audio[\'id\'], "processing_time_ms": update_data["processing_time_ms"],
                    "transcribed": update_data.get("transcribed", False),
                }),
            }).execute()
            PushService.send_push_notification(
                user_id=user_id, title="Audio Processado",
                message=f"Seu audio \'{filename}\' foi limpo e esta pronto.",
                data_payload={"audio_id": audio[\'id\']},
            )
            socketio.emit("audio_completed", {"audio_id": audio[\'id\'], "filename": filename, "message": "Processamento concluido!"}, namespace="/")
        except Exception as e:
            import traceback; traceback.print_exc()
            supabase.table(\'events\').insert({
                "user_id": user_id, "event_type": "AUDIO_PROCESSING_FAILED", "level": "error",
                "screen": "audio", "details_json": json.dumps({"error": str(e)}),
            }).execute()
    return jsonify({"audio": audio}), 201


@audios_bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_audio_offline():
    if \'file\' not in request.files:
        return jsonify({"error": "Nenhum arquivo original enviado"}), 400
    file = request.files[\'file\']
    if file.filename == \'\' or not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".aac")):
        return jsonify({"error": "Arquivo invalido"}), 400
    user_id = get_jwt_identity()
    upload_dir = os.path.join(current_app.root_path, \'..\', \'uploads\')
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, "sync_" + filename)
    file.save(file_path)
    processed_path, processed = None, False
    if \'processed_file\' in request.files:
        pf = request.files[\'processed_file\']
        if pf.filename != \'\':
            pn = "processed_sync_" + secure_filename(pf.filename)
            processed_path = os.path.join(upload_dir, pn)
            pf.save(processed_path)
            processed = True
    transcription = request.form.get("transcription_text", "")
    resp = supabase.table(\'audios\').insert({
        "user_id": user_id, "filename": filename, "file_path": file_path,
        "size_bytes": os.path.getsize(file_path),
        "duration_seconds": request.form.get("duration_seconds", 0, type=int),
        "device_origin": request.form.get("device_origin", "Mobile App (Offline Sync)"),
        "processed": processed, "processed_path": processed_path,
        "processing_time_ms": request.form.get("processing_time_ms", 0, type=int),
        "transcribed": bool(transcription),
        "transcription_text": transcription if transcription else None,
        "favorite": False,
    }).execute()
    audio = resp.data[0]
    supabase.table(\'events\').insert({
        "user_id": user_id, "event_type": "AUDIO_SYNCED_OFFLINE", "level": "info",
        "screen": "audio_sync",
        "details_json": json.dumps({"filename": filename, "processed": processed, "transcribed": bool(transcription)}),
    }).execute()
    return jsonify({"audio": audio, "message": "Audio sincronizado com sucesso (Offline Sync)"}), 201


@audios_bp.route("/", methods=["GET"])
@jwt_required()
def list_audios():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    processed = request.args.get("processed", None)
    favorite = request.args.get("favorite", None)
    offset = (page - 1) * per_page
    q = supabase.table(\'audios\').select(\'*\', count=\'exact\').order(\'recorded_at\', desc=True)
    if processed is not None:
        q = q.eq(\'processed\', processed == "true")
    if favorite is not None:
        q = q.eq(\'favorite\', favorite == "true")
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    return jsonify({
        "audios": resp.data or [], "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1, "page": page,
    })


@audios_bp.route("/", methods=["POST"])
@jwt_required()
def create_audio():
    data = request.get_json()
    resp = supabase.table(\'audios\').insert({
        "user_id": data["user_id"], "filename": data["filename"],
        "file_path": data.get("file_path"),
        "duration_seconds": data.get("duration_seconds", 0),
        "size_bytes": data.get("size_bytes", 0),
        "device_origin": data.get("device_origin"),
        "processed": False, "transcribed": False, "favorite": False,
    }).execute()
    return jsonify({"audio": resp.data[0]}), 201


@audios_bp.route("/<int:audio_id>", methods=["GET"])
@jwt_required()
def get_audio(audio_id):
    resp = supabase.table(\'audios\').select(\'*\').eq(\'id\', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    return jsonify({"audio": resp.data[0]})


@audios_bp.route("/<int:audio_id>", methods=["PUT"])
@jwt_required()
def update_audio(audio_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'audios\').select(\'*\').eq(\'id\', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in ["processed", "transcribed", "favorite", "transcription_text", "playlist_id"]:
        if field in data:
            old_val = audio.get(field)
            new_val = data[field]
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
            update_data[field] = new_val
    if update_data:
        supabase.table(\'audios\').update(update_data).eq(\'id\', audio_id).execute()
    if changes:
        supabase.table(\'events\').insert({
            "user_id": current_user_id, "event_type": "AUDIO_UPDATED", "level": "info",
            "screen": "audios", "details_json": json.dumps({"audio_id": audio_id, "changes": changes}),
        }).execute()
    updated = supabase.table(\'audios\').select(\'*\').eq(\'id\', audio_id).execute().data[0]
    return jsonify({"audio": updated})


@audios_bp.route("/<int:audio_id>", methods=["DELETE"])
@jwt_required()
def delete_audio(audio_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table(\'audios\').select(\'filename\').eq(\'id\', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    filename = resp.data[0][\'filename\']
    supabase.table(\'events\').insert({
        "user_id": current_user_id, "event_type": "AUDIO_DELETED", "level": "warn",
        "screen": "audios", "details_json": json.dumps({"audio_id": audio_id, "filename": filename}),
    }).execute()
    supabase.table(\'audios\').delete().eq(\'id\', audio_id).execute()
    return jsonify({"message": "Audio removido com sucesso"})


@audios_bp.route("/batch-export", methods=["POST"])
@jwt_required()
def batch_export_audios():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    audio_ids = data.get("audio_ids", [])
    if not audio_ids:
        return jsonify({"error": "Nenhum audio selecionado"}), 400
    audios = supabase.table(\'audios\').select(\'*\').in_(\'id\', audio_ids).eq(\'user_id\', current_user_id).execute().data or []
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, \'w\', zipfile.ZIP_DEFLATED) as zf:
        for audio in audios:
            fzip = audio.get(\'processed_path\') if (audio.get(\'processed\') and audio.get(\'processed_path\')) else audio.get(\'file_path\')
            if fzip and os.path.exists(fzip):
                zf.write(fzip, arcname=f"audios/{audio[\'filename\']}")
            if audio.get(\'transcription_text\'):
                txt_name = f"transcriptions/{os.path.splitext(audio[\'filename\'])[0]}.txt"
                zf.writestr(txt_name, audio[\'transcription_text\'])
    memory_file.seek(0)
    return send_file(memory_file, mimetype="application/zip", as_attachment=True, download_name="calmwave_export.zip")
'''

# ── stats.py ──────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'stats.py')] = '''\
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.supabase_ext import supabase
from datetime import datetime, timedelta
import time, random

stats_bp = Blueprint("stats", __name__)


def _count(table, **filters):
    q = supabase.table(table).select(\'*\', count=\'exact\')
    for k, v in filters.items():
        q = q.eq(k, v)
    return q.execute().count or 0


@stats_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    total_audios = _count(\'audios\')
    total_users = _count(\'users\', active=True)
    processed_audios = _count(\'audios\', processed=True)
    total_processed_pct = round((processed_audios / total_audios * 100) if total_audios else 0, 1)

    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_audios = supabase.table(\'audios\').select(\'*\', count=\'exact\').gte(\'recorded_at\', week_ago).execute().count or 0
    last_uploads = supabase.table(\'audios\').select(\'*\').order(\'recorded_at\', desc=True).limit(5).execute().data or []

    from app.routes.streaming import active_sessions
    streaming_sessions_count = len(active_sessions)

    daily_counts = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        cnt = supabase.table(\'audios\').select(\'*\', count=\'exact\').gte(\'recorded_at\', day_start.isoformat()).lt(\'recorded_at\', day_end.isoformat()).execute().count or 0
        daily_counts.append({"day": day.strftime("%a"), "count": cnt})

    return jsonify({
        "total_audios": total_audios, "total_users": total_users,
        "processed_audios": processed_audios, "processed_pct": total_processed_pct,
        "recent_audios_week": recent_audios, "streaming_sessions": streaming_sessions_count,
        "system_status": "Operacional", "daily_counts": daily_counts, "last_uploads": last_uploads,
    })


@stats_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    total_users = _count(\'users\')
    active_users = _count(\'users\', active=True)
    total_audios = _count(\'audios\')
    favorite_audios = _count(\'audios\', favorite=True)
    transcribed_audios = _count(\'audios\', transcribed=True)

    months = []
    for i in range(5, -1, -1):
        ms = (datetime.utcnow().replace(day=1) - timedelta(days=30 * i))
        me = ms + timedelta(days=30)
        cnt = supabase.table(\'users\').select(\'*\', count=\'exact\').gte(\'created_at\', ms.isoformat()).lt(\'created_at\', me.isoformat()).execute().count or 0
        months.append({"month": ms.strftime("%b"), "users": cnt})

    total_processed = _count(\'audios\', processed=True)
    total_transcribed = _count(\'audios\', transcribed=True)
    total_favorites = _count(\'audios\', favorite=True)
    offline_syncs = _count(\'events\', event_type=\'AUDIO_SYNCED_OFFLINE\')
    total_events = max(total_audios, 1)

    def pct(v): return int((v / total_events) * 100)

    features = sorted([
        {"name": "Gravar Audio", "usage": pct(total_audios) or 100},
        {"name": "Limpar Ruido", "usage": pct(total_processed)},
        {"name": "Transcrever", "usage": pct(total_transcribed)},
        {"name": "Marcar Favorito", "usage": pct(total_favorites)},
        {"name": "Sincronizacao Offline", "usage": pct(offline_syncs)},
        {"name": "Criar Playlist", "usage": pct(int(total_audios * 0.3))},
    ], key=lambda x: x["usage"], reverse=True)

    device_performance = [
        {"device": "Samsung S23", "time": "0.15s", "pct": 90},
        {"device": "Xiaomi Redmi Note 11", "time": "0.25s", "pct": 70},
        {"device": "Motorola Moto G8", "time": "0.45s", "pct": 45},
    ]
    try:
        from collections import Counter
        dev_data = supabase.table(\'user_devices\').select(\'device_name\').execute().data or []
        if dev_data:
            counts = Counter(d.get(\'device_name\', \'Unknown\') for d in dev_data).most_common(3)
            mock_t = [("0.15s", 90), ("0.25s", 70), ("0.45s", 45)]
            device_performance = [{"device": n, "time": mock_t[i][0], "pct": mock_t[i][1]} for i, (n, _) in enumerate(counts)]
            while len(device_performance) < 3:
                device_performance.append({"device": "Samsung S23", "time": "0.15s", "pct": 90})
    except Exception:
        pass

    r1, r7, r30 = (80, 50, 30) if active_users > 0 else (0, 0, 0)
    return jsonify({
        "total_active_users": active_users, "total_users": total_users,
        "session_duration": "4m 32s", "bounce_rate": 42.8,
        "total_audios": total_audios, "favorite_audios": favorite_audios, "transcribed_audios": transcribed_audios,
        "user_growth": months, "features_usage": features, "device_performance": device_performance,
        "retention": [{"day": "Dia 1", "rate": r1}, {"day": "Dia 7", "rate": r7}, {"day": "Dia 30", "rate": r30}],
    })


@stats_bp.route("/status", methods=["GET"])
@jwt_required()
def system_status():
    db_status, db_latency = "online", 0
    try:
        start = time.time()
        supabase.table(\'users\').select(\'id\').limit(1).execute()
        db_latency = int((time.time() - start) * 1000)
    except Exception:
        db_status = "danger"

    from app.routes.streaming import active_sessions
    lp_status, lp_latency = "online", 0
    try:
        import urllib.request
        lp_start = time.time()
        req = urllib.request.Request("https://calmwave-landingpage.vercel.app/", headers={"User-Agent": "Mozilla/5.0"})
        resp_lp = urllib.request.urlopen(req, timeout=5)
        lp_latency = int((time.time() - lp_start) * 1000)
        if resp_lp.getcode() != 200:
            lp_status = "danger"
    except Exception:
        lp_status = "danger"

    services = [
        {"name": "Landing Page", "status": lp_status, "uptime": "99.99%", "latency": f"{lp_latency}ms", "icon": "🌐"},
        {"name": "API Principal", "status": "online", "uptime": "99.98%", "latency": f"{random.randint(20,60)}ms", "icon": "⚡"},
        {"name": "Processamento de Audio", "status": "online", "uptime": "99.95%", "latency": f"{random.randint(100,200)}ms", "icon": "🎙️"},
        {"name": "Transcricao IA", "status": "online", "uptime": "99.80%", "latency": f"{random.randint(200,400)}ms", "icon": "📝"},
        {"name": "Streaming WebSocket", "status": "online", "uptime": "99.90%", "latency": f"{random.randint(10,30)}ms", "icon": "📡"},
        {"name": "Banco de Dados", "status": db_status, "uptime": "99.99%", "latency": f"{db_latency}ms", "icon": "🗄️"},
        {"name": "Armazenamento Local", "status": "online", "uptime": "99.97%", "latency": f"{random.randint(5,15)}ms", "icon": "☁️"},
    ]
    overall = "danger" if any(s["status"]=="danger" for s in services) else "warn" if any(s["status"]=="warn" for s in services) else "online"
    online_count = sum(1 for s in services if s["status"] == "online")
    avg_lat = sum(int(s["latency"].replace("ms","")) for s in services) // len(services)
    return jsonify({
        "overall_status": overall, "services": services, "incidents": [],
        "metrics": {"online_count": online_count, "total_count": len(services), "avg_latency": f"{avg_lat}ms", "uptime_30d": "99.94%"},
    })
'''

# ── admin.py ──────────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'admin.py')] = '''\
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
from datetime import datetime, timedelta
from collections import Counter
import bcrypt, json

admin_bp = Blueprint("admin", __name__)


def _get_role(user_id):
    resp = supabase.table(\'users\').select(\'role,account_type\').eq(\'id\', user_id).execute()
    return resp.data[0] if resp.data else None

def is_admin(user_id):
    u = _get_role(user_id)
    return u and u.get(\'role\') in (\'admin\', \'super_admin\')

def is_super_admin(user_id):
    u = _get_role(user_id)
    return u and u.get(\'role\') == \'super_admin\'

def _safe_user(u):
    u.pop(\'password_hash\', None)
    return u

def _count(table, **filters):
    q = supabase.table(table).select(\'*\', count=\'exact\')
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
    q = supabase.table(\'users\').select(\'*\', count=\'exact\').order(\'created_at\', desc=True)
    if search:
        q = q.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    if acct:
        q = q.eq(\'account_type\', acct)
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
    if supabase.table(\'users\').select(\'id\').eq(\'email\', data[\'email\']).execute().data:
        return jsonify({"error": "Email ja cadastrado"}), 409
    pw_hash = bcrypt.hashpw(data[\'password\'].encode(), bcrypt.gensalt()).decode()
    resp = supabase.table(\'users\').insert({
        "name": data["name"], "email": data["email"], "password_hash": pw_hash,
        "account_type": data.get("account_type", "free"), "role": data.get("role", "user"), "active": True,
    }).execute()
    user = _safe_user(resp.data[0])
    supabase.table(\'events\').insert({
        "user_id": cid, "event_type": "ADMIN_USER_CREATED", "level": "info", "screen": "admin",
        "details_json": json.dumps({"target_user_id": user[\'id\'], "email": user[\'email\'], "account_type": user[\'account_type\']}),
    }).execute()
    return jsonify({"user": user}), 201


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def admin_update_user(user_id):
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    resp = supabase.table(\'users\').select(\'*\').eq(\'id\', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in [\'name\', \'account_type\', \'active\']:
        if field in data and user.get(field) != data[field]:
            changes[field] = {"old": user.get(field), "new": data[field]}
            update_data[field] = data[field]
    if "role" in data and user[\'role\'] != data["role"]:
        if not is_super_admin(cid) and (data["role"] in ["admin","super_admin"] or user[\'role\'] in ["admin","super_admin"]):
            return jsonify({"error": "Apenas Super Admins podem alterar papeis restritos."}), 403
        changes["role"] = {"old": user[\'role\'], "new": data["role"]}
        update_data["role"] = data["role"]
    if update_data:
        supabase.table(\'users\').update(update_data).eq(\'id\', user_id).execute()
    if changes:
        supabase.table(\'events\').insert({
            "user_id": cid, "event_type": "ADMIN_USER_UPDATED", "level": "info", "screen": "admin",
            "details_json": json.dumps({"target_user_id": user_id, "changes": changes}),
        }).execute()
    updated = _safe_user(supabase.table(\'users\').select(\'*\').eq(\'id\', user_id).execute().data[0])
    return jsonify({"user": updated})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id):
    cid = get_jwt_identity()
    if not is_admin(cid):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403
    if cid == user_id:
        return jsonify({"error": "Voce nao pode deletar sua propria conta"}), 400
    resp = supabase.table(\'users\').select(\'email\').eq(\'id\', user_id).execute()
    if not resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    email = resp.data[0][\'email\']
    supabase.table(\'users\').update({"active": False}).eq(\'id\', user_id).execute()
    supabase.table(\'events\').insert({
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
            "total": _count(\'users\'), "active": _count(\'users\', active=True),
            "admins": _count(\'users\', account_type=\'admin\'), "premium": _count(\'users\', account_type=\'premium\'),
            "free": _count(\'users\', account_type=\'free\'),
        },
        "audios": {
            "total": _count(\'audios\'), "processed": _count(\'audios\', processed=True),
            "processed_pct": round((_count(\'audios\', processed=True) / max(_count(\'audios\'), 1)) * 100, 1),
            "transcribed": _count(\'audios\', transcribed=True), "favorite": _count(\'audios\', favorite=True),
        },
        "metrics": {
            "avg_audios_per_user": round(_count(\'audios\') / max(_count(\'users\', active=True), 1), 2),
            "total_events": _count(\'events\'), "error_events": _count(\'events\', level=\'error\'),
        },
        "today": {
            "audios": supabase.table(\'audios\').select(\'*\', count=\'exact\').gte(\'recorded_at\', today).execute().count or 0,
            "registrations": supabase.table(\'users\').select(\'*\', count=\'exact\').gte(\'created_at\', today).execute().count or 0,
            "events": supabase.table(\'events\').select(\'*\', count=\'exact\').gte(\'created_at\', today).execute().count or 0,
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
        cnt = supabase.table(\'users\').select(\'*\', count=\'exact\').gte(\'created_at\', ds.isoformat()).lt(\'created_at\', de.isoformat()).execute().count or 0
        daily_registrations.append({"day": day.strftime("%a"), "count": cnt})
    users_data = supabase.table(\'users\').select(\'id,name,email\').execute().data or []
    user_audio_counts = []
    for u in users_data:
        cnt = supabase.table(\'audios\').select(\'*\', count=\'exact\').eq(\'user_id\', u[\'id\']).execute().count or 0
        user_audio_counts.append({"id": u[\'id\'], "name": u[\'name\'], "email": u[\'email\'], "audio_count": cnt})
    top_users = sorted(user_audio_counts, key=lambda x: x[\'audio_count\'], reverse=True)[:10]
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
        cnt = supabase.table(\'audios\').select(\'*\', count=\'exact\').gte(\'recorded_at\', ds.isoformat()).lt(\'recorded_at\', de.isoformat()).execute().count or 0
        daily_uploads.append({"day": day.strftime("%a"), "count": cnt})
    processed_data = supabase.table(\'audios\').select(\'processing_time_ms\').eq(\'processed\', True).execute().data or []
    total_pt = sum((a.get(\'processing_time_ms\') or 0) for a in processed_data)
    pc = len(processed_data)
    all_audios = supabase.table(\'audios\').select(\'size_bytes\').execute().data or []
    total_size = sum((a.get(\'size_bytes\') or 0) for a in all_audios)
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
    q = supabase.table(\'events\').select(\'*\', count=\'exact\').order(\'created_at\', desc=True)
    if level:
        q = q.eq(\'level\', level)
    if event_type:
        q = q.eq(\'event_type\', event_type)
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    all_ev = supabase.table(\'events\').select(\'event_type\').execute().data or []
    dist = Counter(e[\'event_type\'] for e in all_ev).most_common(10)
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
    notif = supabase.table(\'notifications\').insert({
        "user_id": None, "title": data["title"], "message": data["message"],
        "type": data.get("type", "info"), "is_read": False,
    }).execute()
    supabase.table(\'events\').insert({
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
    if not supabase.table(\'notifications\').select(\'id\').eq(\'id\', notification_id).execute().data:
        return jsonify({"error": "Notificacao nao encontrada"}), 404
    supabase.table(\'notifications\').delete().eq(\'id\', notification_id).execute()
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
    resp = supabase.table(\'events\').select(\'*\', count=\'exact\').like(\'event_type\', \'ADMIN_%\').order(\'created_at\', desc=True).range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    return jsonify({
        "logs": resp.data or [], "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    })
'''

# ── streaming.py ──────────────────────────────────────────────────────────────
files[os.path.join(BASE, 'streaming.py')] = '''\
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.supabase_ext import supabase
import time
from datetime import datetime
import os, base64, json

streaming_bp = Blueprint("streaming", __name__)

try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None
    print("Warning: Audio processor not available")

active_sessions = {}


@streaming_bp.route("/sessions", methods=["GET"])
def get_sessions():
    sessions_list = []
    for sid, data in active_sessions.items():
        duration_seconds = int(time.time() - data["start_time"])
        m, s = divmod(duration_seconds, 60)
        sessions_list.append({
            "id": sid, "user": data.get("user", "Anonymous"),
            "device": data.get("device", "Unknown"),
            "connected_at": data["connected_at"],
            "duration": f"{m}m {s}s",
            "messages": data.get("messages", 0),
            "status": "online",
        })
    return jsonify({"sessions": sessions_list})


@socketio.on(\'connect\')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on(\'disconnect\')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in active_sessions:
        del active_sessions[request.sid]
        socketio.emit(\'session_update\', {\'action\': \'remove\', \'id\': request.sid})


@socketio.on(\'start_stream\')
def handle_start_stream(data):
    sid = request.sid
    upload_dir = os.path.join(current_app.root_path, \'..\', \'uploads\')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"stream_{sid}_{int(time.time())}.wav"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, \'wb\') as f:
        pass
    active_sessions[sid] = {
        "id": sid, "user": data.get("user", "Anonymous"), "device": data.get("device", "Unknown"),
        "start_time": time.time(), "connected_at": datetime.utcnow().isoformat() + "Z",
        "messages": 0, "file_path": file_path, "filename": filename,
    }
    try:
        supabase.table(\'events\').insert({
            "user_id": 1, "event_type": "STREAMING_START", "level": "info", "screen": "streaming",
            "details_json": json.dumps({"session_id": sid, "device": data.get("device", "Unknown")}),
        }).execute()
    except Exception as e:
        print(f"Error logging stream start: {e}")
    socketio.emit(\'session_update\', {\'action\': \'add\', \'session\': active_sessions[sid], \'id\': sid})
    return {"status": "ok", "message": "Stream started"}


@socketio.on(\'audio_chunk\')
def handle_audio_chunk(data):
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid]["messages"] += 1
        if "audio_data" in data:
            try:
                audio_bytes = base64.b64decode(data["audio_data"])
                with open(active_sessions[sid]["file_path"], \'ab\') as f:
                    f.write(audio_bytes)
            except Exception as e:
                print(f"Error saving audio chunk: {e}")
        if active_sessions[sid]["messages"] % 5 == 0:
            socketio.emit(\'session_stats\', {
                \'id\': sid, \'messages\': active_sessions[sid]["messages"],
                \'active_sessions\': len(active_sessions),
                \'messages_per_min\': sum(s.get("messages", 0) for s in active_sessions.values()) * 2,
                \'latency_ms\': 12, \'bandwidth_mbps\': round(len(active_sessions) * 0.5, 1),
            })
    return {"status": "ok"}


@socketio.on(\'stop_stream\')
def handle_stop_stream():
    sid = request.sid
    if sid in active_sessions:
        session_data = active_sessions[sid]
        try:
            user_id = 1
            file_path = session_data["file_path"]
            size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            duration = int(time.time() - session_data["start_time"])
            if size_bytes > 0:
                audio_resp = supabase.table(\'audios\').insert({
                    "user_id": user_id, "filename": session_data["filename"],
                    "file_path": file_path, "size_bytes": size_bytes,
                    "duration_seconds": duration,
                    "device_origin": session_data["device"] + " (Stream)",
                    "processed": False, "transcribed": False, "favorite": False,
                }).execute()
                audio = audio_resp.data[0]
                supabase.table(\'events\').insert({
                    "user_id": user_id, "event_type": "STREAMING_STOP", "level": "info", "screen": "streaming",
                    "details_json": json.dumps({
                        "session_id": sid, "duration_seconds": duration,
                        "size_bytes": size_bytes, "audio_id": audio.get(\'id\'),
                    }),
                }).execute()
                if denoiser and denoiser.model is not None:
                    try:
                        start_p = time.time()
                        with open(file_path, \'rb\') as f:
                            raw = f.read()
                        processed_bytes = denoiser.denoise_audio(raw)
                        pname = f"processed_{session_data[\'filename\']}"
                        ppath = os.path.join(os.path.dirname(file_path), pname)
                        with open(ppath, \'wb\') as f:
                            f.write(processed_bytes)
                        update_data = {
                            "processed": True, "processed_path": ppath,
                            "processing_time_ms": int((time.time() - start_p) * 1000),
                        }
                        if transcribe_audio:
                            u_r = supabase.table(\'users\').select(\'transcription_language\').eq(\'id\', user_id).execute()
                            lang = u_r.data[0].get(\'transcription_language\', \'pt-BR\') if u_r.data else \'pt-BR\'
                            tx = transcribe_audio(ppath, language=lang)
                            if tx:
                                update_data["transcribed"] = True
                                update_data["transcription_text"] = tx
                        supabase.table(\'audios\').update(update_data).eq(\'id\', audio[\'id\']).execute()
                        notif = supabase.table(\'notifications\').insert({
                            "user_id": 1,
                            "title": "Audio Processado pela IA",
                            "message": f"A transmissao ao vivo do dispositivo {session_data[\'device\']} foi processada.",
                            "type": "success", "is_read": False,
                        }).execute()
                        socketio.emit(\'new_notification\', notif.data[0])
                    except Exception as e:
                        print(f"Error processing streamed audio: {e}")
        except Exception as e:
            print(f"Error saving stream: {e}")
        del active_sessions[sid]
        socketio.emit(\'session_update\', {\'action\': \'remove\', \'id\': sid})
    return {"status": "ok"}
'''

# Write all files
for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Written: {path}")

print("\nAll route files migrated to Supabase REST API!")
