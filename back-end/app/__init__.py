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

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS(app, resources={r"/api/*": {"origins": [frontend_url, "http://localhost:5000"]}})

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    limiter.init_app(app)

    # Celery Init
    from app.celery_ext import celery_app
    app.config.update(
        CELERY_BROKER_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery_app.conf.update(app.config)

    # Tratar Erros Globais (Item 3) e Logs de Sistema
    from werkzeug.exceptions import HTTPException
    from flask import jsonify, request
    from app.models.other import Event
    import json
    import logging

    @app.after_request
    def log_response(response):
        if request.path.startswith('/api/') and not request.path.endswith('/logs'):
            # Omit noisy routes like events/logs polling if any, but log API hits
            pass
        return response

    @app.errorhandler(Exception)
    def handle_exception(e):
        try:
            from app.models.other import Event
            import json
            error_details = {"error": str(e), "url": request.url, "method": request.method}
            evt = Event(
                event_type="SYSTEM_ERROR", 
                level="error", 
                screen="backend", 
                details_json=json.dumps(error_details)
            )
            db.session.add(evt)
            db.session.commit()
        except:
            db.session.rollback()

        if isinstance(e, HTTPException):
            return jsonify({"error": getattr(e, "description", "Erro HTTP"), "status": e.code}), e.code
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
        db.create_all()
        _ensure_legacy_schema()
        _seed_admin()

    return app


def _seed_admin():
    """Cria admin padrão se não existir."""
    from app.models.user import User
    import bcrypt

    if not User.query.filter_by(email="admin@calmwave.com").first():
        pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        admin = User(
            email="admin@calmwave.com",
            password_hash=pw,
            name="Admin",
            account_type="premium",
            role="super_admin",
        )
        db.session.add(admin)
        db.session.commit()


def _ensure_legacy_schema():
    """Aplica ajustes mínimos de schema em bancos SQLite antigos."""
    engine = db.engine
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "users" not in tables:
        return

    current_columns = {col["name"] for col in inspector.get_columns("users")}
    columns_to_add = [
        ("profile_photo_url", "VARCHAR(500)"),
        ("last_access", "DATETIME"),
        ("active", "BOOLEAN DEFAULT 1"),
        ("account_type", "VARCHAR(50) DEFAULT 'free'"),
        ("role", "VARCHAR(50) DEFAULT 'user'"),
        ("dark_mode", "BOOLEAN DEFAULT 0"),
        ("notifications_enabled", "BOOLEAN DEFAULT 1"),
        ("auto_process_audio", "BOOLEAN DEFAULT 1"),
        ("audio_quality", "VARCHAR(20) DEFAULT 'high'"),
    ]

    for column_name, column_def in columns_to_add:
        if column_name in current_columns:
            continue
        db.session.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))

    db.session.commit()
