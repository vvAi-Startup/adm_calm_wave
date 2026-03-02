from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, UserDevice, UserAchievement
from app.models.other import Event
from datetime import datetime
import json

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "")

    query = User.query
    if search:
        query = query.filter(
            db.or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )

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
    )


@users_bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"user": user.to_dict()})


@users_bp.route("/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    changes = {}
    if "name" in data and user.name != data["name"]:
        changes["name"] = {"old": user.name, "new": data["name"]}
        user.name = data["name"]
    if "active" in data and user.active != data["active"]:
        changes["active"] = {"old": user.active, "new": data["active"]}
        user.active = data["active"]
    if "account_type" in data and user.account_type != data["account_type"]:
        changes["account_type"] = {"old": user.account_type, "new": data["account_type"]}
        user.account_type = data["account_type"]
    if "profile_photo_url" in data:
        user.profile_photo_url = data["profile_photo_url"]
        
    # Log event
    if changes:
        update_event = Event(
            user_id=current_user_id,
            event_type="USER_UPDATED",
            level="info",
            screen="users",
            details_json=json.dumps({"target_user_id": user_id, "changes": changes})
        )
        db.session.add(update_event)
        
    db.session.commit()
    return jsonify({"user": user.to_dict()})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    user.active = False
    
    # Log event
    delete_event = Event(
        user_id=current_user_id,
        event_type="USER_DEACTIVATED",
        level="warn",
        screen="users",
        details_json=json.dumps({"target_user_id": user_id, "email": user.email})
    )
    db.session.add(delete_event)
    
    db.session.commit()
    return jsonify({"message": "Usuário desativado com sucesso"})

@users_bp.route("/me/settings", methods=["PUT"])
@jwt_required()
def update_my_settings():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
        
    data = request.get_json()
    if 'dark_mode' in data:
        user.dark_mode = data['dark_mode']
    if 'notifications_enabled' in data:
        user.notifications_enabled = data['notifications_enabled']
    if 'auto_process_audio' in data:
        user.auto_process_audio = data['auto_process_audio']
    if 'audio_quality' in data:
        user.audio_quality = data['audio_quality']
    
    if "name" in data:
        user.name = data["name"]
        
    db.session.commit()
    return jsonify({"user": user.to_dict()})

@users_bp.route("/me/devices", methods=["GET"])
@jwt_required()
def get_my_devices():
    current_user_id = get_jwt_identity()
    devices = UserDevice.query.filter_by(user_id=current_user_id).order_by(UserDevice.last_active.desc()).all()
    
    # If no devices exist for some reason, create a mock one for the current user
    if not devices:
        new_device = UserDevice(
            user_id=current_user_id,
            device_name=request.headers.get("User-Agent", "Navegador Web")[:255],
            device_type="Desktop",
            ip_address=request.remote_addr,
            is_current=True
        )
        db.session.add(new_device)
        db.session.commit()
        devices = [new_device]
        
    return jsonify({"devices": [d.to_dict() for d in devices]})

@users_bp.route("/me/devices/<int:device_id>", methods=["DELETE"])
@jwt_required()
def revoke_device(device_id):
    current_user_id = get_jwt_identity()
    device = UserDevice.query.filter_by(id=device_id, user_id=current_user_id).first()
    
    if not device:
        return jsonify({"error": "Dispositivo não encontrado"}), 404
        
    db.session.delete(device)
    db.session.commit()
    
    # Revoking all logic if it's not specific device
    return jsonify({"success": True})

@users_bp.route("/me/devices/revoke_all", methods=["POST"])
@jwt_required()
def revoke_all_devices():
    current_user_id = get_jwt_identity()
    UserDevice.query.filter_by(user_id=current_user_id, is_current=False).delete()
    db.session.commit()
    return jsonify({"success": True})

@users_bp.route("/me/achievements", methods=["GET"])
@jwt_required()
def get_my_achievements():
    current_user_id = get_jwt_identity()
    
    # We will compute achievements on the fly for demonstration and save them
    from app.models.audio import Audio
    total_audios = Audio.query.filter_by(user_id=current_user_id).count()
    processed_audios = Audio.query.filter_by(user_id=current_user_id, processed=True).count()
    
    unlocked = UserAchievement.query.filter_by(user_id=current_user_id).all()
    unlocked_ids = [a.achievement_id for a in unlocked]
    
    achievements_metadata = [
        {"id": 1, "icon": "🎙️", "name": "Primeira Gravação", "desc": "Gravou o primeiro áudio no app", "requirement": 1},
        {"id": 2, "icon": "🎖️", "name": "10 Gravações", "desc": "Gravou 10 áudios", "requirement": 10},
        {"id": 3, "icon": "🔥", "name": "7 Dias Seguidos", "desc": "Usou o app por 7 dias consecutivos", "requirement": 7},
        {"id": 4, "icon": "🎵", "name": "50 Áudios Limpos", "desc": "Processou 50 áudios com IA", "requirement": 50},
    ]
    
    results = []
    for meta in achievements_metadata:
        earned = meta["id"] in unlocked_ids
        
        # Check if they should have earned it now
        if not earned:
            if meta["id"] == 1 and total_audios >= 1:
                earned = True
            elif meta["id"] == 2 and total_audios >= 10:
                earned = True
            elif meta["id"] == 4 and processed_audios >= 50:
                earned = True
                
            if earned:
                new_ach = UserAchievement(user_id=current_user_id, achievement_id=meta["id"])
                db.session.add(new_ach)
                
        results.append({
            "id": meta["id"],
            "icon": meta["icon"],
            "name": meta["name"],
            "desc": meta["desc"],
            "earned": earned,
            "count": total_audios if meta["id"] in [1, 2] else (processed_audios if meta["id"] == 4 else 1)
        })
        
    db.session.commit()
    return jsonify({"achievements": results})
