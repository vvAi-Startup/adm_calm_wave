import sys

path = 'c:/Users/fatec-dsm6/Desktop/adm_calm_wave/back-end/app/__init__.py'
c = open(path, 'r', encoding='utf-8').read()

err_handlers = """
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
"""

c = c.replace('socketio.init_app(app)', 'socketio.init_app(app)\n' + err_handlers)

open(path, 'w', encoding='utf-8').write(c)
print("OK")
