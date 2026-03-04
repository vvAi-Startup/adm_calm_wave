from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.audio import Audio
from app.models.other import Event, Statistic, Notification
from datetime import datetime, timedelta
from sqlalchemy import func
import bcrypt
import json

admin_bp = Blueprint("admin", __name__)


def is_admin(user_id):
    """Check if user is admin"""
    user = User.query.get(user_id)
    return user and user.role in ["admin", "super_admin"]

def is_super_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == "super_admin"


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def admin_list_users():
    """List all users (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")
    account_type = request.args.get("account_type", None)

    query = User.query
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )
    if account_type:
        query = query.filter(User.account_type == account_type)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "users": [u.to_dict() for u in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
        }
    ), 200


@admin_bp.route("/users", methods=["POST"])
@jwt_required()
def admin_create_user():
    """Create a new user (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    data = request.get_json()
    required = ["name", "email", "password"]
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Nome, email e senha são obrigatórios"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email já cadastrado"}), 409

    pw_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=pw_hash,
        account_type=data.get("account_type", "free"),
        role=data.get("role", "user"),
    )
    db.session.add(user)
    db.session.flush()

    # Log admin creation event
    creation_event = Event(
        user_id=current_user_id,
        event_type="ADMIN_USER_CREATED",
        level="info",
        screen="admin",
        details_json=json.dumps(
            {
                "target_user_id": user.id,
                "email": user.email,
                "account_type": user.account_type,
            }
        ),
    )
    db.session.add(creation_event)
    db.session.commit()

    return jsonify({"user": user.to_dict()}), 201


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def admin_update_user(user_id):
    """Update a user (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    changes = {}
    if "name" in data and user.name != data["name"]:
        changes["name"] = {"old": user.name, "new": data["name"]}
        user.name = data["name"]

    if "account_type" in data and user.account_type != data["account_type"]:
        changes["account_type"] = {"old": user.account_type, "new": data["account_type"]}
        user.account_type = data["account_type"]

    if "role" in data and user.role != data["role"]:
        # Only super_admin can change roles to/from admin
        if not is_super_admin(current_user_id) and (data["role"] in ["admin", "super_admin"] or user.role in ["admin", "super_admin"]):
            return jsonify({"error": "Apenas Super Admins podem alterar papéis restritos."}), 403
        changes["role"] = {"old": user.role, "new": data["role"]}
        user.role = data["role"]

    if "active" in data and user.active != data["active"]:
        changes["active"] = {"old": user.active, "new": data["active"]}
        user.active = data["active"]

    if changes:
        update_event = Event(
            user_id=current_user_id,
            event_type="ADMIN_USER_UPDATED",
            level="info",
            screen="admin",
            details_json=json.dumps({"target_user_id": user_id, "changes": changes}),
        )
        db.session.add(update_event)

    db.session.commit()
    return jsonify({"user": user.to_dict()})


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    if current_user_id == user_id:
        return jsonify({"error": "Você não pode deletar sua própria conta"}), 400

    user = User.query.get_or_404(user_id)
    user.active = False

    # Log deletion event
    deletion_event = Event(
        user_id=current_user_id,
        event_type="ADMIN_USER_DELETED",
        level="warn",
        screen="admin",
        details_json=json.dumps({"target_user_id": user_id, "email": user.email}),
    )
    db.session.add(deletion_event)
    db.session.commit()

    return jsonify({"message": "Usuário deletado com sucesso"})


@admin_bp.route("/reports/overview", methods=["GET"])
@jwt_required()
def admin_report_overview():
    """Get system overview report (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    admin_users = User.query.filter_by(account_type="admin").count()
    premium_users = User.query.filter_by(account_type="premium").count()
    free_users = User.query.filter_by(account_type="free").count()

    total_audios = Audio.query.count()
    processed_audios = Audio.query.filter_by(processed=True).count()
    transcribed_audios = Audio.query.filter_by(transcribed=True).count()
    favorite_audios = Audio.query.filter_by(favorite=True).count()

    # Average metrics
    avg_audios_per_user = (
        total_audios / active_users if active_users > 0 else 0
    )
    total_events = Event.query.count()
    error_events = Event.query.filter_by(level="error").count()

    # Today's activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_audios = Audio.query.filter(Audio.recorded_at >= today_start).count()
    today_registrations = User.query.filter(User.created_at >= today_start).count()
    today_events = Event.query.filter(Event.created_at >= today_start).count()

    return jsonify(
        {
            "users": {
                "total": total_users,
                "active": active_users,
                "admins": admin_users,
                "premium": premium_users,
                "free": free_users,
            },
            "audios": {
                "total": total_audios,
                "processed": processed_audios,
                "processed_pct": round(
                    (processed_audios / total_audios * 100) if total_audios > 0 else 0, 1
                ),
                "transcribed": transcribed_audios,
                "favorite": favorite_audios,
            },
            "metrics": {
                "avg_audios_per_user": round(avg_audios_per_user, 2),
                "total_events": total_events,
                "error_events": error_events,
            },
            "today": {
                "audios": today_audios,
                "registrations": today_registrations,
                "events": today_events,
            },
        }
    )


@admin_bp.route("/reports/users", methods=["GET"])
@jwt_required()
def admin_report_users():
    """Get detailed user statistics report (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    # Users created last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    daily_registrations = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = User.query.filter(
            User.created_at >= day_start, User.created_at < day_end
        ).count()
        daily_registrations.append({"day": day.strftime("%a"), "count": count})

    # Most active users (by audio count)
    active_users = (
        db.session.query(User.id, User.name, User.email, func.count(Audio.id))
        .outerjoin(Audio)
        .group_by(User.id)
        .order_by(func.count(Audio.id).desc())
        .limit(10)
        .all()
    )

    top_users = [
        {"id": u[0], "name": u[1], "email": u[2], "audio_count": u[3]}
        for u in active_users
    ]

    return jsonify(
        {
            "daily_registrations": daily_registrations,
            "top_users": top_users,
        }
    )


@admin_bp.route("/reports/audios", methods=["GET"])
@jwt_required()
def admin_report_audios():
    """Get detailed audio statistics report (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    # Daily audio uploads last 7 days
    daily_uploads = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Audio.query.filter(
            Audio.recorded_at >= day_start, Audio.recorded_at < day_end
        ).count()
        daily_uploads.append({"day": day.strftime("%a"), "count": count})

    # Processing statistics
    total_processed_time = (
        db.session.query(func.sum(Audio.processing_time_ms))
        .filter(Audio.processing_time_ms.isnot(None))
        .scalar()
        or 0
    )
    processed_count = Audio.query.filter(Audio.processed == True).count()
    avg_processing_time = (
        (total_processed_time / processed_count) if processed_count > 0 else 0
    )

    # Total storage used
    total_size = (
        db.session.query(func.sum(Audio.size_bytes)).scalar() or 0
    )

    return jsonify(
        {
            "daily_uploads": daily_uploads,
            "processing": {
                "total_processed": processed_count,
                "total_processing_time_ms": int(total_processed_time),
                "avg_processing_time_ms": round(avg_processing_time, 2),
            },
            "storage": {
                "total_bytes": total_size,
                "total_mb": round(total_size / (1024 * 1024), 2),
                "total_gb": round(total_size / (1024 * 1024 * 1024), 2),
            },
        }
    )


@admin_bp.route("/reports/events", methods=["GET"])
@jwt_required()
def admin_report_events():
    """Get event logs report (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    level = request.args.get("level", None)
    event_type = request.args.get("event_type", None)

    query = Event.query
    if level:
        query = query.filter(Event.level == level)
    if event_type:
        query = query.filter(Event.event_type == event_type)

    # Event distribution
    event_distribution = (
        db.session.query(Event.event_type, func.count(Event.id))
        .group_by(Event.event_type)
        .order_by(func.count(Event.id).desc())
        .limit(10)
        .all()
    )

    pagination = query.order_by(Event.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify(
        {
            "events": [e.to_dict() for e in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
            "distribution": [
                {"event_type": e[0], "count": e[1]} for e in event_distribution
            ],
        }
    )


@admin_bp.route("/notifications/broadcast", methods=["POST"])
@jwt_required()
def admin_broadcast_notification():
    """Send a notification to all users (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    data = request.get_json()
    required = ["title", "message"]
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Título e mensagem são obrigatórios"}), 400

    notification = Notification(
        user_id=None,  # System-wide
        title=data["title"],
        message=data["message"],
        type=data.get("type", "info"),
    )
    db.session.add(notification)

    # Log event
    broadcast_event = Event(
        user_id=current_user_id,
        event_type="ADMIN_BROADCAST",
        level="info",
        screen="admin",
        details_json=json.dumps({"title": data["title"], "message": data["message"]}),
    )
    db.session.add(broadcast_event)
    db.session.commit()

    return jsonify({"notification": notification.to_dict()}), 201


@admin_bp.route("/notifications/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def admin_delete_notification(notification_id):
    """Delete a notification (admin only)"""
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas administradores podem acessar."}), 403

    notification = Notification.query.get_or_404(notification_id)
    db.session.delete(notification)
    db.session.commit()

    return jsonify({"message": "Notificação deletada com sucesso"})


@admin_bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def admin_audit_logs():
    """Get audit logs (super_admin only)"""
    current_user_id = get_jwt_identity()
    if not is_super_admin(current_user_id):
        return jsonify({"error": "Acesso negado. Apenas super administradores."}), 403

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Filter events generated by admin actions
    query = Event.query.filter(
        Event.event_type.like("ADMIN_%")
    ).order_by(Event.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    })
