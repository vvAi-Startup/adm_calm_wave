from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///calmwave.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # Celery Init
    from app.celery_ext import celery_app
    app.config.update(
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_RESULT_BACKEND='redis://localhost:6379/0'
    )
    celery_app.conf.update(app.config)

    # Tratar Erros Globais (Item 3)
    from werkzeug.exceptions import HTTPException
    from flask import jsonify

    @app.errorhandler(Exception)
    def handle_exception(e):
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

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(audios_bp, url_prefix="/api/audios")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(streaming_bp, url_prefix="/api/streaming")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(playlists_bp, url_prefix="/api/playlists")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    with app.app_context():
        db.create_all()
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
            account_type="admin",
        )
        db.session.add(admin)
        db.session.commit()
