import json
import subprocess
import tempfile
import os

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

def api(method, path, body=None):
    url = f"https://api.render.com/v1{path}"
    cmd = [
        "curl.exe", "-s", "-X", method, url,
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
    ]
    tmp = None
    if body:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(body, tmp, ensure_ascii=False)
        tmp.close()
        cmd += ["-d", f"@{tmp.name}"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if tmp:
        os.unlink(tmp.name)
    raw = result.stdout.strip()
    if not raw:
        print(f"  STDERR: {result.stderr}")
        return None
    data = json.loads(raw)
    if isinstance(data, dict) and "message" in data and len(data) == 1:
        print(f"  ERROR: {data['message']}")
        return None
    return data

# 1. Redis já existe — buscar connection string interna
print(f"=== 1. Redis: {REDIS_ID} ===")
redis_conn = api("GET", f"/redis/{REDIS_ID}/connection-info")
if redis_conn:
    redis_url = redis_conn.get("internalConnectionString", "")
    print(f"  REDIS_URL (internal): {redis_url[:30]}...")
else:
    print("  Não foi possível obter connection info — usando placeholder")
    redis_url = "redis://calm-wave-redis:6379"

# 2. Criar Web Service
print("\n=== 2. Criando Web Service (calm-wave-api) ===")
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
    "name": "calm-wave-api",
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
if web:
    svc = web.get("service") or web
    web_id = svc.get("id", "")
    web_url = (svc.get("serviceDetails") or {}).get("url", "")
    print(f"  Criado! ID: {web_id}")
    print(f"  URL: {web_url}")
    print(f"  Dashboard: {svc.get('dashboardUrl','')}")
else:
    print("  FALHOU")
    web_id = None

# 3. Criar Worker Celery
print("\n=== 3. Criando Worker Celery ===")
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
    "name": "calm-wave-celery-worker",
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
if worker:
    wrk = worker.get("service") or worker
    worker_id = wrk.get("id", "")
    print(f"  Criado! ID: {worker_id}")
    print(f"  Dashboard: {wrk.get('dashboardUrl','')}")
else:
    print("  FALHOU")
    worker_id = None

print("\n" + "="*50)
print("RESUMO")
print(f"  Redis ID   : {REDIS_ID}")
print(f"  Web ID     : {web_id}")
print(f"  Worker ID  : {worker_id}")
print(f"  REDIS_URL  : {redis_url[:40]}...")


# Redis já criado anteriormente
redis_id = "red-d6nml54hg0os73c7d4l0"
print(f"=== 1. Redis já existe: {redis_id} ===")

# Obter connectionString do Redis
print("  Buscando connectionString do Redis...")
redis_info = api("GET", f"/redis/{redis_id}")
if redis_info:
    conn_str = redis_info.get("connectionInfo", {})
    print(f"  Info: {json.dumps(redis_info, indent=2)}")
else:
    print("  Não foi possível buscar info do Redis, continuando sem REDIS_URL automático")
    conn_str = None

# 2. Criar Web Service (API)
print("\n=== 2. Criando Web Service (calm-wave-api) ===")
env_vars_web = [
    {"key": "PYTHON_VERSION", "value": "3.10.14"},
    {"key": "FLASK_ENV", "value": "production"},
    {"key": "FLASK_DEBUG", "value": "0"},
    {"key": "SUPABASE_URL", "value": SUPABASE_URL},
    {"key": "SUPABASE_KEY", "value": SUPABASE_KEY},
    {"key": "DATABASE_URL", "value": DATABASE_URL},
    {"key": "JWT_SECRET_KEY", "generateValue": True},
    {"key": "REDIS_URL", "fromCache": {"id": redis_id, "property": "connectionString"}},
]

web = api("POST", "/services", {
    "autoDeploy": "yes",
    "branch": BRANCH,
    "name": "calm-wave-api",
    "ownerId": OWNER_ID,
    "region": "ohio",
    "plan": "starter",
    "repo": REPO,
    "rootDir": "back-end",
    "type": "web_service",
    "runtime": "python",
    "serviceDetails": {
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "gunicorn --worker-class eventlet -w 1 --timeout 120 run:app",
        "healthCheckPath": "/api/health",
        "pullRequestPreviewsEnabled": "no",
    },
    "envVars": env_vars_web,
})
if web:
    web_id = (web.get("service") or {}).get("id") or web.get("id")
    web_url = (web.get("service") or {}).get("serviceDetails", {}).get("url", "")
    print(f"  Web Service criado: {web_id}")
    print(f"  URL: {web_url}")
    print(f"  Resposta: {json.dumps(web, indent=2)}")
else:
    print("  Falha ao criar Web Service")
    web_id = None

# 3. Criar Worker Celery
print("\n=== 3. Criando Worker Celery ===")
env_vars_worker = [
    {"key": "PYTHON_VERSION", "value": "3.10.14"},
    {"key": "SUPABASE_URL", "value": SUPABASE_URL},
    {"key": "SUPABASE_KEY", "value": SUPABASE_KEY},
    {"key": "DATABASE_URL", "value": DATABASE_URL},
    {"key": "REDIS_URL", "fromCache": {"id": redis_id, "property": "connectionString"}},
]

worker = api("POST", "/services", {
    "autoDeploy": "yes",
    "branch": BRANCH,
    "name": "calm-wave-celery-worker",
    "ownerId": OWNER_ID,
    "region": "ohio",
    "plan": "starter",
    "repo": REPO,
    "rootDir": "back-end",
    "type": "background_worker",
    "runtime": "python",
    "serviceDetails": {
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "celery -A run.celery worker --loglevel=info",
    },
    "envVars": env_vars_worker,
})
if worker:
    worker_id = (worker.get("service") or {}).get("id") or worker.get("id")
    print(f"  Worker criado: {worker_id}")
    print(f"  Resposta: {json.dumps(worker, indent=2)}")
else:
    print("  Falha ao criar Worker")
    worker_id = None

print("\n=== Resumo ===")
print(f"Redis ID   : {redis_id}")
print(f"Web ID     : {web_id}")
print(f"Worker ID  : {worker_id}")
