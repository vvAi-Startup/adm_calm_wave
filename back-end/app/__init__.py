from flask import Flask, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
import os
from sqlalchemy import inspect, text

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///calmwave.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    from datetime import timedelta
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

    # Origens permitidas: CORS_ORIGINS (vírgula) + FRONTEND_URL + próprio host no Render + localhost
    _allowed = {"http://localhost:3000", "http://localhost:5000"}
    if os.getenv("FRONTEND_URL"):
        _allowed.add(os.getenv("FRONTEND_URL"))
    if os.getenv("RENDER_EXTERNAL_URL"):
        _allowed.add(os.getenv("RENDER_EXTERNAL_URL"))
    if os.getenv("CORS_ORIGINS"):
        for origin in os.getenv("CORS_ORIGINS").split(","):
            _allowed.add(origin.strip())
    CORS(app, resources={r"/api/*": {"origins": list(_allowed)}})


    db.init_app(app)
    from app.supabase_ext import init_supabase
    init_supabase(app)
    jwt.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)

    # Tratar Erros Globais e Logs de Sistema
    from werkzeug.exceptions import HTTPException
    from flask import jsonify, request
    import json
    import logging

    @app.after_request
    def log_response(response):
        if request.path.startswith('/api/') and not request.path.endswith('/logs'):
            pass
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        try:
            from app.supabase_ext import supabase as _sb
            if _sb is not None:
                error_details = {"error": str(e), "url": request.url, "method": request.method}
                _sb.table('events').insert({
                    "event_type": "SYSTEM_ERROR",
                    "level": "error",
                    "screen": "backend",
                    "details_json": json.dumps(error_details),
                }).execute()
        except Exception:
            pass

        if isinstance(e, HTTPException):
            return jsonify({"error": getattr(e, "description", "Erro HTTP"), "status": e.code}), e.code
        logging.getLogger(__name__).exception("Unhandled exception")
        return jsonify({"error": "Erro interno do servidor", "message": str(e), "status": 500}), 500

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso não encontrado", "status": 404}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Requisição inválida", "status": 400}), 400

    
    # Servir arquivo estático openapi.json
    @app.route('/api/docs/openapi.json')
    def swagger_json():
        docs_dir = os.path.abspath(os.path.join(app.root_path, '..', 'docs'))
        return send_from_directory(docs_dir, 'openapi.json')

    # Configurar Swagger UI
    SWAGGER_URL = '/docs'
    API_URL = '/api/docs/openapi.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "CalmWave API Documentation"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.audios import audios_bp
    from app.routes.stats import stats_bp
    from app.routes.events import events_bp
    from app.routes.streaming import streaming_bp
    from app.routes.notifications import notifications_bp
    from app.routes.playlists import playlists_bp
    from app.routes.admin import admin_bp
    from app.routes.support import support_bp
    from app.routes.privacy import privacy_bp
    from app.routes.billing import billing_bp
    from app.routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(audios_bp, url_prefix="/api/audios")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(streaming_bp, url_prefix="/api/streaming")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(playlists_bp, url_prefix="/api/playlists")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(support_bp, url_prefix="/api/support")
    app.register_blueprint(privacy_bp, url_prefix="/api/privacy")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")

    with app.app_context():
        _seed_admin()

    return app


def _seed_admin():
    """Cria admin padrão via Supabase se não existir."""
    import bcrypt
    from app.supabase_ext import supabase
    if supabase is None:
        return
    try:
        existing = supabase.table('users').select('id').eq('email', 'admin@calmwave.com').execute()
        if not existing.data:
            pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
            supabase.table('users').insert({
                'email': 'admin@calmwave.com',
                'password_hash': pw,
                'name': 'Admin',
                'account_type': 'premium',
                'role': 'super_admin',
            }).execute()
    except BaseException as e:
        print(f'[seed_admin] Aviso: nao foi possivel verificar/criar admin - {type(e).__name__}: {e}')
