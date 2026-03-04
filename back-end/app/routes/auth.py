from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.auth import LoginSchema, RegisterSchema
from app import db
from app.models.user import User, UserDevice
from app.models.other import Event
from datetime import datetime
import bcrypt
import json

auth_bp = Blueprint("auth", __name__)


from app import limiter

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")  # Rate limit contra brute force
def login():
    try:
        data = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Parâmetros inválidos", "messages": err.messages}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not bcrypt.checkpw(data["password"].encode(), user.password_hash.encode()):
        return jsonify({"error": "Credenciais inválidas"}), 401
        return jsonify({"error": "Credenciais inválidas"}), 401

    if not user.active:
        return jsonify({"error": "Conta desativada"}), 403

    user.last_access = datetime.utcnow()
    
    # Track device session
    user_agent = request.headers.get("User-Agent", "Navegador Web")
    ip_addr = request.remote_addr
    
    # Mark old same-ip/same-device as not current
    UserDevice.query.filter_by(user_id=user.id, is_current=True).update({"is_current": False})
    
    new_device = UserDevice(
        user_id=user.id,
        device_name=user_agent[:255],
        device_type="Desktop" if "Windows" in user_agent or "Macintosh" in user_agent else "Mobile",
        ip_address=ip_addr,
        is_current=True
    )
    db.session.add(new_device)
    
    # Log login event
    login_event = Event(
        user_id=user.id,
        event_type="USER_LOGIN",
        level="info",
        screen="auth",
        details_json=json.dumps({"email": user.email})
    )
    db.session.add(login_event)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({"token": token, "refresh_token": refresh_token, "user": user.to_dict()}), 200


@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = RegisterSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Parametros invalidos", "messages": err.messages}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email já cadastrado"}), 409

    pw_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=pw_hash,
        account_type=data.get("account_type", "free"),
        role="user",
    )
    db.session.add(user)
    db.session.flush() # Get user ID without committing yet
    
    # Log register event
    register_event = Event(
        user_id=user.id,
        event_type="USER_REGISTERED",
        level="info",
        screen="auth",
        details_json=json.dumps({"email": user.email, "account_type": user.account_type})
    )
    db.session.add(register_event)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({"token": token, "refresh_token": refresh_token, "user": user.to_dict()}), 201


@auth_bp.route("/me", methods=["GET"])
def me():
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify({"user": user.to_dict()}), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({"token": new_access_token}), 200
