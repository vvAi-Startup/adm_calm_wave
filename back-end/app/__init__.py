from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
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

    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.audios import audios_bp
    from app.routes.stats import stats_bp
    from app.routes.events import events_bp
    from app.routes.streaming import streaming_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(audios_bp, url_prefix="/api/audios")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(events_bp, url_prefix="/api/events")
    app.register_blueprint(streaming_bp, url_prefix="/api/streaming")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

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
