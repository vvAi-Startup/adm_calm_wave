from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.other import SupportTicket, TicketMessage
from app.models.user import User
from app.services.push_service import PushService

support_bp = Blueprint("support", __name__)

@support_bp.route("/", methods=["GET"])
@jwt_required()
def list_tickets():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # If admin, see all. If user, see only theirs.
    if user.account_type == "admin":
        tickets = SupportTicket.query.order_by(SupportTicket.updated_at.desc()).all()
    else:
        tickets = SupportTicket.query.filter_by(user_id=current_user_id).order_by(SupportTicket.updated_at.desc()).all()
        
    results = []
    for t in tickets:
        t_dict = t.to_dict()
        u = User.query.get(t.user_id)
        t_dict["user_email"] = u.email if u else "Desconhecido"
        
        # Get last message
        last_msg = TicketMessage.query.filter_by(ticket_id=t.id).order_by(TicketMessage.sent_at.desc()).first()
        t_dict["last_message"] = last_msg.message if last_msg else "Sem mensagens"
        
        results.append(t_dict)
        
    return jsonify({"tickets": results})

@support_bp.route("/", methods=["POST"])
@jwt_required()
def create_ticket():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    subject = data.get("subject", "Sem Assunto")
    message = data.get("message", "")
    
    ticket = SupportTicket(user_id=current_user_id, subject=subject, status="open")
    db.session.add(ticket)
    db.session.commit()
    
    if message:
        t_msg = TicketMessage(ticket_id=ticket.id, sender="user", message=message)
        db.session.add(t_msg)
        db.session.commit()
        
    return jsonify({"ticket": ticket.to_dict()}), 201

@support_bp.route("/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if user.account_type != "admin" and ticket.user_id != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403
        
    messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.sent_at.asc()).all()
    
    t_dict = ticket.to_dict()
    ticket_user = User.query.get(ticket.user_id)
    t_dict["user_email"] = ticket_user.email if ticket_user else "Desconhecido"
    t_dict["messages_list"] = [m.to_dict() for m in messages]
    
    return jsonify({"ticket": t_dict})

@support_bp.route("/<int:ticket_id>/reply", methods=["POST"])
@jwt_required()
def reply_ticket(ticket_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if user.account_type != "admin" and ticket.user_id != current_user_id:
        return jsonify({"error": "Acesso negado"}), 403
        
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400
        
    sender = "admin" if user.account_type == "admin" else "user"
    
    t_msg = TicketMessage(ticket_id=ticket.id, sender=sender, message=message)
    db.session.add(t_msg)
    
    # Update ticket status
    if sender == "admin":
        ticket.status = "answered"
    else:
        ticket.status = "open"
        
    db.session.commit()
    
    # Push Notification to mobile user if it's admin replying
    if sender == "admin":
        PushService.send_push_notification(
            user_id=ticket.user_id,
            title=f"Atualização no Chamado #{ticket.id}",
            message=f"Suporte: {message[:50]}...",
            data_payload={"ticket_id": ticket.id}
        )
        
    return jsonify({"message": t_msg.to_dict()}), 201
