from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.other import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()
    notifications = Notification.query.filter(
        (Notification.user_id == current_user_id) | (Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    return jsonify([n.to_dict() for n in notifications]), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    current_user_id = get_jwt_identity()
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id is not None and notification.user_id != current_user_id:
        return jsonify({"error": "Acesso nao autorizado"}), 403
    notification.is_read = True
    db.session.commit()
    return jsonify({"message": "Notificacao lida", "notification": notification.to_dict()}), 200

@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    current_user_id = get_jwt_identity()
    notifications = Notification.query.filter(
        (Notification.user_id == current_user_id) | (Notification.user_id == None),
        Notification.is_read == False
    ).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return jsonify({"message": "Todas as notificacoes lidas"}), 200
