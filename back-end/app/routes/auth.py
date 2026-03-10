from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.auth import LoginSchema, RegisterSchema
from app.supabase_ext import supabase
from datetime import datetime
import bcrypt
import json

auth_bp = Blueprint('auth', __name__)
from app import limiter

@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    try:
        data = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'error': 'Parâmetros inválidos', 'messages': err.messages}), 400

    response = supabase.table('users').select('*').eq('email', data['email']).execute()
    users = response.data

    if not users or not bcrypt.checkpw(data['password'].encode(), users[0]['password_hash'].encode()):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    user = users[0]

    if not user.get('active', True):
        return jsonify({'error': 'Conta desativada'}), 403

    supabase.table('users').update({'last_access': datetime.utcnow().isoformat()}).eq('id', user['id']).execute()

    user_agent = request.headers.get('User-Agent', 'Navegador Web')
    ip_addr = request.remote_addr

    supabase.table('user_devices').update({'is_current': False}).eq('user_id', user['id']).eq('is_current', True).execute()
    
    supabase.table('user_devices').insert({
        'user_id': user['id'],
        'device_name': user_agent[:255],
        'device_type': 'Desktop' if 'Windows' in user_agent or 'Macintosh' in user_agent else 'Mobile',
        'ip_address': ip_addr,
        'is_current': True
    }).execute()

    supabase.table('events').insert({
        'user_id': user['id'],
        'event_type': 'USER_LOGIN',
        'level': 'info',
        'screen': 'auth',
        'details_json': json.dumps({'email': user['email']})
    }).execute()

    token = create_access_token(identity=str(user['id']))
    refresh_token = create_refresh_token(identity=str(user['id']))
    return jsonify({'token': token, 'refresh_token': refresh_token, 'user': user}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = RegisterSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({'error': 'Parametros invalidos', 'messages': err.messages}), 400

    existing = supabase.table('users').select('*').eq('email', data['email']).execute().data
    if existing:
        return jsonify({'error': 'Email já cadastrado'}), 409

    pw_hash = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    
    new_user_res = supabase.table('users').insert({
        'name': data['name'],
        'email': data['email'],
        'password_hash': pw_hash,
        'account_type': data.get('account_type', 'free'),
        'role': 'user',
    }).execute()
    
    user = new_user_res.data[0]

    supabase.table('events').insert({
        'user_id': user['id'],
        'event_type': 'USER_REGISTERED',
        'level': 'info',
        'screen': 'auth',
        'details_json': json.dumps({'email': user['email'], 'account_type': user.get('account_type')})
    }).execute()

    token = create_access_token(identity=str(user['id']))
    refresh_token = create_refresh_token(identity=str(user['id']))
    return jsonify({'token': token, 'refresh_token': refresh_token, 'user': user}), 201

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user_res = supabase.table('users').select('*').eq('id', user_id).execute()
    if not user_res.data:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify({'user': user_res.data[0]}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({'token': new_access_token}), 200
