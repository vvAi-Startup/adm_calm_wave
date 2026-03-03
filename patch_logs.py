import os
import re

# 1. FIX FRONTEND: Remove MOCK_EVENTS from web/app/logs/page.tsx
frontend_path = r'c:\Users\fatec-dsm6\Desktop\adm_calm_wave\web\app\logs\page.tsx'
with open(frontend_path, 'r', encoding='utf-8') as f:
    front_content = f.read()

# Remove the MOCK_EVENTS array entirely
front_content = re.sub(r'const MOCK_EVENTS: Event\[\] = \[\s*\{.*?\}\s*,?\s*\];', '', front_content, flags=re.DOTALL)
front_content = re.sub(r'\.catch\(\(\) => setEvents\(MOCK_EVENTS\)\)', r'.catch((err) => { console.error(err); setEvents([]); })', front_content)

with open(frontend_path, 'w', encoding='utf-8') as f:
    f.write(front_content)

# 2. FIX BACKEND: Add logging interceptors to app/__init__.py
backend_path = r'c:\Users\fatec-dsm6\Desktop\adm_calm_wave\back-end\app\__init__.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    back_content = f.read()

if 'from flask import request' not in back_content:
    back_content = back_content.replace('from flask import jsonify', 'from flask import jsonify, request')

logging_block = """
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
"""

# Replace existing error handler block
back_content = re.sub(
    r'\# Tratar Erros Globais \(Item 3\).*?return jsonify.*?500', 
    logging_block.strip() + '\n', 
    back_content, 
    flags=re.DOTALL
)

with open(backend_path, 'w', encoding='utf-8') as f:
    f.write(back_content)

print("Logs interceptors and frontend mocks patched successfully.")
