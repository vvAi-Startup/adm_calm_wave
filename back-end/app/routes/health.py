from flask import Blueprint, jsonify
import time
import os

health_bp = Blueprint('health', __name__)

_start_time = time.time()

@health_bp.route('/health', methods=['GET'])
def health_check():
    uptime = int(time.time() - _start_time)
    db_ok = _check_db()
    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "service": "calm-wave-api",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "database": "ok" if db_ok else "unreachable",
        "timestamp": time.time(),
    }), 200 if db_ok else 503


def _check_db():
    try:
        from app.supabase_ext import supabase
        if supabase is None:
            return False
        supabase.table('users').select('id').limit(1).execute()
        return True
    except Exception:
        return False
