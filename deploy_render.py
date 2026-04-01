import json
import os
import sys

try:
    import requests
except ImportError:
    print("Por favor, instale a biblioteca requests: pip install requests")
    sys.exit(1)

def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


API_KEY = _required_env("RENDER_API_KEY")
OWNER_ID = _required_env("RENDER_OWNER_ID")
REPO = os.getenv("RENDER_REPO", "https://github.com/vvAi-Startup/adm_calm_wave")
BRANCH = os.getenv("RENDER_BRANCH", "deploy-render")
REDIS_ID = _required_env("RENDER_REDIS_ID")

SUPABASE_URL = _required_env("SUPABASE_URL")
SUPABASE_KEY = _required_env("SUPABASE_KEY")
DATABASE_URL = _required_env("DATABASE_URL")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def api(method, path, body=None):
    url = f"https://api.render.com/v1{path}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=body)
        else:
            print(f"Método {method} não suportado.")
            return None
            
        if response.status_code >= 400:
            print(f"  API ERROR ({response.status_code}): {response.text}")
            try:
                data = response.json()
                if "message" in data:
                    print(f"  MESSAGE: {data['message']}")
            except:
                pass
            return None
            
        return response.json()
    except Exception as e:
        print(f"  EXCEPTION chamando API: {e}")
        return None

print(f"=== 1. Obter Connection String do Redis ({REDIS_ID}) ===")
redis_conn = api("GET", f"/redis/{REDIS_ID}/connection-info")
redis_url = "redis://calm-wave-redis:6379"
if redis_conn:
    redis_url = redis_conn.get("internalConnectionString", redis_url)
    print(f"  REDIS_URL: {redis_url[:30]}...")

print("\n=== 2. Criar Web Service (API) ===")
env_vars_web = [
    {"key": "PYTHON_VERSION", "value": "3.10.14"},
    {"key": "FLASK_ENV", "value": "production"},
    {"key": "FLASK_DEBUG", "value": "0"},
    {"key": "SUPABASE_URL", "value": SUPABASE_URL},
    {"key": "SUPABASE_KEY", "value": SUPABASE_KEY},
    {"key": "DATABASE_URL", "value": DATABASE_URL},
    {"key": "JWT_SECRET_KEY", "generateValue": True},
    {"key": "REDIS_URL", "value": redis_url},
]

web = api("POST", "/services", {
    "autoDeploy": "yes",
    "branch": BRANCH,
    "name": "calm-wave-api-main",
    "ownerId": OWNER_ID,
    "repo": REPO,
    "rootDir": "back-end",
    "type": "web_service",
    "envVars": env_vars_web,
    "serviceDetails": {
        "runtime": "python",
        "plan": "starter",
        "region": "ohio",
        "healthCheckPath": "/api/health",
        "pullRequestPreviewsEnabled": "no",
        "envSpecificDetails": {
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "gunicorn --worker-class eventlet -w 1 --timeout 120 run:app",
        },
    },
})
web_id = None
if web:
    svc = web.get("service", web)
    web_id = svc.get("id", "")
    print(f"  Criado! ID: {web_id}")
    print(f"  URL: {(svc.get('serviceDetails') or {}).get('url', '')}")
else:
    print("  FALHOU")

print("\n=== 3. Criar Celery Worker ===")
env_vars_worker = [
    {"key": "PYTHON_VERSION", "value": "3.10.14"},
    {"key": "SUPABASE_URL", "value": SUPABASE_URL},
    {"key": "SUPABASE_KEY", "value": SUPABASE_KEY},
    {"key": "DATABASE_URL", "value": DATABASE_URL},
    {"key": "REDIS_URL", "value": redis_url},
]

worker = api("POST", "/services", {
    "autoDeploy": "yes",
    "branch": BRANCH,
    "name": "calm-wave-worker-main",
    "ownerId": OWNER_ID,
    "repo": REPO,
    "rootDir": "back-end",
    "type": "background_worker",
    "envVars": env_vars_worker,
    "serviceDetails": {
        "runtime": "python",
        "plan": "starter",
        "region": "ohio",
        "envSpecificDetails": {
            "buildCommand": "pip install -r requirements.txt",
            "startCommand": "celery -A run.celery worker --loglevel=info",
        },
    },
})
worker_id = None
if worker:
    wrk = worker.get("service", worker)
    worker_id = wrk.get("id", "")
    print(f"  Criado! ID: {worker_id}")
else:
    print("  FALHOU")

print("\n=== FINAL ===")
print(f"Web ID: {web_id}, Worker ID: {worker_id}")
