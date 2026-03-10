from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
from app.services.push_service import PushService

support_bp = Blueprint("support", __name__)


def _is_admin_user(user):
    return user.get('account_type') == 'admin' or user.get('role') in ('admin', 'super_admin')


def _ticket_with_count(t):
    count = supabase.table('ticket_messages').select('id', count='exact').eq('ticket_id', t['id']).execute().count or 0
    t['messages_count'] = count
    return t


@support_bp.route("/", methods=["GET"])
@jwt_required()
def list_tickets():
    current_user_id = get_jwt_identity()
    u_resp = supabase.table('users').select('account_type,role').eq('id', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    if _is_admin_user(user):
        tickets = supabase.table('support_tickets').select('*').order('updated_at', desc=True).execute().data or []
    else:
        tickets = supabase.table('support_tickets').select('*').eq('user_id', current_user_id).order('updated_at', desc=True).execute().data or []

    results = []
    for t in tickets:
        t = _ticket_with_count(t)
        eu = supabase.table('users').select('email').eq('id', t['user_id']).execute()
        t['user_email'] = eu.data[0]['email'] if eu.data else 'Desconhecido'
        lm = supabase.table('ticket_messages').select('message').eq('ticket_id', t['id']).order('sent_at', desc=True).limit(1).execute()
        t['last_message'] = lm.data[0]['message'] if lm.data else 'Sem mensagens'
        results.append(t)
    return jsonify({"tickets": results})


@support_bp.route("/", methods=["POST"])
@jwt_required()
def create_ticket():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    subject = data.get("subject", "Sem Assunto")
    message = data.get("message", "")

    resp = supabase.table('support_tickets').insert({
        "user_id": current_user_id,
        "subject": subject,
        "status": "open",
    }).execute()
    ticket = _ticket_with_count(resp.data[0])

    if message:
        supabase.table('ticket_messages').insert({
            "ticket_id": ticket['id'],
            "sender": "user",
            "message": message,
        }).execute()
    return jsonify({"ticket": ticket}), 201


@support_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    u_resp = supabase.table('users').select('account_type,role').eq('id', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    t_resp = supabase.table('support_tickets').select('*').eq('id', ticket_id).execute()
    if not t_resp.data:
        return jsonify({"error": "Ticket nao encontrado"}), 404
    ticket = t_resp.data[0]

    if not _is_admin_user(user) and ticket['user_id'] != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403

    messages = supabase.table('ticket_messages').select('*').eq('ticket_id', ticket_id).order('sent_at', desc=False).execute().data or []
    eu = supabase.table('users').select('email').eq('id', ticket['user_id']).execute()
    ticket['user_email'] = eu.data[0]['email'] if eu.data else 'Desconhecido'
    ticket['messages_list'] = messages
    ticket = _ticket_with_count(ticket)
    return jsonify({"ticket": ticket})


@support_bp.route("/<int:ticket_id>/reply", methods=["POST"])
@jwt_required()
def reply_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    u_resp = supabase.table('users').select('account_type,role').eq('id', current_user_id).execute()
    if not u_resp.data:
        return jsonify({"error": "Usuario nao encontrado"}), 404
    user = u_resp.data[0]

    t_resp = supabase.table('support_tickets').select('*').eq('id', ticket_id).execute()
    if not t_resp.data:
        return jsonify({"error": "Ticket nao encontrado"}), 404
    ticket = t_resp.data[0]

    if not _is_admin_user(user) and ticket['user_id'] != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    sender = "admin" if _is_admin_user(user) else "user"
    msg_resp = supabase.table('ticket_messages').insert({
        "ticket_id": ticket_id,
        "sender": sender,
        "message": message,
    }).execute()
    new_status = "answered" if sender == "admin" else "open"
    supabase.table('support_tickets').update({"status": new_status}).eq('id', ticket_id).execute()

    if sender == "admin":
        PushService.send_push_notification(
            user_id=ticket['user_id'],
            title=f"Atualizacao no Chamado #{ticket_id}",
            message=f"Suporte: {message[:50]}...",
            data_payload={"ticket_id": ticket_id},
        )
    return jsonify({"message": msg_resp.data[0]}), 201
