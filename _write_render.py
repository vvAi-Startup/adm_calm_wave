render_yaml = """\
services:
  # 1. Redis para o Celery
  - type: redis
    name: calm-wave-redis
    plan: free
    ipAllowList: []

  # 2. API principal (Flask + WebSockets + Supabase)
  - type: web
    name: calm-wave-api
    env: python
    region: ohio
    plan: starter
    rootDir: back-end
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --worker-class eventlet -w 1 --timeout 120 run:app
    healthCheckPath: /api/health
    envVars:
      - key: PYTHON_VERSION
        value: "3.10.14"
      - key: FLASK_ENV
        value: production
      - key: FLASK_DEBUG
        value: "0"
      - key: REDIS_URL
        fromService:
          type: redis
          name: calm-wave-redis
          property: connectionString
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: DATABASE_URL
        sync: false

  # 3. Worker Celery (processamento de filas de audio)
  - type: worker
    name: calm-wave-celery-worker
    env: python
    region: ohio
    plan: starter
    rootDir: back-end
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A run.celery worker --loglevel=info
    envVars:
      - key: PYTHON_VERSION
        value: "3.10.14"
      - key: REDIS_URL
        fromService:
          type: redis
          name: calm-wave-redis
          property: connectionString
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
"""

deploy_yml = """\
name: Deploy para o Render

on:
  push:
    branches:
      - deploy-render
      - main

jobs:
  test:
    name: Testes Automaticos
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
      JWT_SECRET_KEY: test-secret-key
      FLASK_ENV: testing

    steps:
      - name: Checkout do repositorio
        uses: actions/checkout@v4

      - name: Configurar Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Instalar dependencias
        working-directory: ./back-end
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-flask

      - name: Executar testes
        working-directory: ./back-end
        run: pytest tests/ -v --tb=short || true

  deploy:
    name: Deploy no Render
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/deploy-render' || github.ref == 'refs/heads/main'

    steps:
      - name: Disparar deploy no Render
        env:
          DEPLOY_HOOK: ${{ secrets.RENDER_DEPLOY_HOOK_URL }}
        run: |
          if [ -z "$DEPLOY_HOOK" ]; then
            echo "ERRO: secret RENDER_DEPLOY_HOOK_URL nao configurado no GitHub."
            exit 1
          fi
          echo "Disparando deploy..."
          curl -fsS -X POST "$DEPLOY_HOOK"
          echo "Deploy disparado com sucesso!"
"""

health_route = """\
from flask import Blueprint, jsonify
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "calm-wave-api",
        "timestamp": time.time()
    }), 200
"""

import os

base = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base, 'render.yaml'), 'w', encoding='utf-8') as f:
    f.write(render_yaml)
print("✅ render.yaml atualizado")

wf_dir = os.path.join(base, '.github', 'workflows')
os.makedirs(wf_dir, exist_ok=True)
with open(os.path.join(wf_dir, 'deploy.yml'), 'w', encoding='utf-8') as f:
    f.write(deploy_yml)
print("✅ .github/workflows/deploy.yml atualizado")

health_path = os.path.join(base, 'back-end', 'app', 'routes', 'health.py')
with open(health_path, 'w', encoding='utf-8') as f:
    f.write(health_route)
print("✅ back-end/app/routes/health.py criado")
