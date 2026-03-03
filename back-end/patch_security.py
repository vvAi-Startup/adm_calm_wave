import os

path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/__init__.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Setup Limiter
imports = "from flask import Flask, send_from_directory"
new_imports = imports + "\nfrom flask_limiter import Limiter\nfrom flask_limiter.util import get_remote_address"
text = text.replace(imports, new_imports)

init_limiter = "db = SQLAlchemy()\njwt = JWTManager()\nsocketio = SocketIO(cors_allowed_origins='*')"
new_init = init_limiter + "\nlimiter = Limiter(key_func=get_remote_address, default_limits=['500 per day', '100 per hour'])"
text = text.replace(init_limiter, new_init)

app_init = "db.init_app(app)\n    jwt.init_app(app)\n    socketio.init_app(app)"
new_app_init = app_init + "\n    limiter.init_app(app)"
text = text.replace(app_init, new_app_init)


# Configure CORS securely
old_cors = 'CORS(app, resources={r"/api/*": {"origins": "*"}})'
new_cors = 'frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")\n    CORS(app, resources={r"/api/*": {"origins": [frontend_url, "http://localhost:5000"]}})'
text = text.replace(old_cors, new_cors)


with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

# Protect specific auth route
auth_path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/routes/auth.py'
with open(auth_path, 'r', encoding='utf-8') as f:
    auth_text = f.read()

auth_text = auth_text.replace(
    '@auth_bp.route("/login", methods=["POST"])',
    'from app import limiter\n\n@auth_bp.route("/login", methods=["POST"])\n@limiter.limit("5 per minute")  # Rate limit contra brute force'
)

with open(auth_path, 'w', encoding='utf-8') as f:
    f.write(auth_text)

print("Backend security patched")
