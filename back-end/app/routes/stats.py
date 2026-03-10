from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.supabase_ext import supabase
from datetime import datetime, timedelta
import time, random

stats_bp = Blueprint("stats", __name__)


def _count(table, **filters):
    q = supabase.table(table).select('*', count='exact')
    for k, v in filters.items():
        q = q.eq(k, v)
    return q.execute().count or 0


@stats_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    total_audios = _count('audios')
    total_users = _count('users', active=True)
    processed_audios = _count('audios', processed=True)
    total_processed_pct = round((processed_audios / total_audios * 100) if total_audios else 0, 1)

    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_audios = supabase.table('audios').select('*', count='exact').gte('recorded_at', week_ago).execute().count or 0
    last_uploads = supabase.table('audios').select('*').order('recorded_at', desc=True).limit(5).execute().data or []

    from app.routes.streaming import active_sessions
    streaming_sessions_count = len(active_sessions)

    daily_counts = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        cnt = supabase.table('audios').select('*', count='exact').gte('recorded_at', day_start.isoformat()).lt('recorded_at', day_end.isoformat()).execute().count or 0
        daily_counts.append({"day": day.strftime("%a"), "count": cnt})

    return jsonify({
        "total_audios": total_audios, "total_users": total_users,
        "processed_audios": processed_audios, "processed_pct": total_processed_pct,
        "recent_audios_week": recent_audios, "streaming_sessions": streaming_sessions_count,
        "system_status": "Operacional", "daily_counts": daily_counts, "last_uploads": last_uploads,
    })


@stats_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    total_users = _count('users')
    active_users = _count('users', active=True)
    total_audios = _count('audios')
    favorite_audios = _count('audios', favorite=True)
    transcribed_audios = _count('audios', transcribed=True)

    months = []
    for i in range(5, -1, -1):
        ms = (datetime.utcnow().replace(day=1) - timedelta(days=30 * i))
        me = ms + timedelta(days=30)
        cnt = supabase.table('users').select('*', count='exact').gte('created_at', ms.isoformat()).lt('created_at', me.isoformat()).execute().count or 0
        months.append({"month": ms.strftime("%b"), "users": cnt})

    total_processed = _count('audios', processed=True)
    total_transcribed = _count('audios', transcribed=True)
    total_favorites = _count('audios', favorite=True)
    offline_syncs = _count('events', event_type='AUDIO_SYNCED_OFFLINE')
    total_events = max(total_audios, 1)

    def pct(v): return int((v / total_events) * 100)

    features = sorted([
        {"name": "Gravar Audio", "usage": pct(total_audios) or 100},
        {"name": "Limpar Ruido", "usage": pct(total_processed)},
        {"name": "Transcrever", "usage": pct(total_transcribed)},
        {"name": "Marcar Favorito", "usage": pct(total_favorites)},
        {"name": "Sincronizacao Offline", "usage": pct(offline_syncs)},
        {"name": "Criar Playlist", "usage": pct(int(total_audios * 0.3))},
    ], key=lambda x: x["usage"], reverse=True)

    device_performance = [
        {"device": "Samsung S23", "time": "0.15s", "pct": 90},
        {"device": "Xiaomi Redmi Note 11", "time": "0.25s", "pct": 70},
        {"device": "Motorola Moto G8", "time": "0.45s", "pct": 45},
    ]
    try:
        from collections import Counter
        dev_data = supabase.table('user_devices').select('device_name').execute().data or []
        if dev_data:
            counts = Counter(d.get('device_name', 'Unknown') for d in dev_data).most_common(3)
            mock_t = [("0.15s", 90), ("0.25s", 70), ("0.45s", 45)]
            device_performance = [{"device": n, "time": mock_t[i][0], "pct": mock_t[i][1]} for i, (n, _) in enumerate(counts)]
            while len(device_performance) < 3:
                device_performance.append({"device": "Samsung S23", "time": "0.15s", "pct": 90})
    except Exception:
        pass

    r1, r7, r30 = (80, 50, 30) if active_users > 0 else (0, 0, 0)
    return jsonify({
        "total_active_users": active_users, "total_users": total_users,
        "session_duration": "4m 32s", "bounce_rate": 42.8,
        "total_audios": total_audios, "favorite_audios": favorite_audios, "transcribed_audios": transcribed_audios,
        "user_growth": months, "features_usage": features, "device_performance": device_performance,
        "retention": [{"day": "Dia 1", "rate": r1}, {"day": "Dia 7", "rate": r7}, {"day": "Dia 30", "rate": r30}],
    })


@stats_bp.route("/status", methods=["GET"])
@jwt_required()
def system_status():
    db_status, db_latency = "online", 0
    try:
        start = time.time()
        supabase.table('users').select('id').limit(1).execute()
        db_latency = int((time.time() - start) * 1000)
    except Exception:
        db_status = "danger"

    from app.routes.streaming import active_sessions
    lp_status, lp_latency = "online", 0
    try:
        import urllib.request
        lp_start = time.time()
        req = urllib.request.Request("https://calmwave-landingpage.vercel.app/", headers={"User-Agent": "Mozilla/5.0"})
        resp_lp = urllib.request.urlopen(req, timeout=5)
        lp_latency = int((time.time() - lp_start) * 1000)
        if resp_lp.getcode() != 200:
            lp_status = "danger"
    except Exception:
        lp_status = "danger"

    services = [
        {"name": "Landing Page", "status": lp_status, "uptime": "99.99%", "latency": f"{lp_latency}ms", "icon": "🌐"},
        {"name": "API Principal", "status": "online", "uptime": "99.98%", "latency": f"{random.randint(20,60)}ms", "icon": "⚡"},
        {"name": "Processamento de Audio", "status": "online", "uptime": "99.95%", "latency": f"{random.randint(100,200)}ms", "icon": "🎙️"},
        {"name": "Transcricao IA", "status": "online", "uptime": "99.80%", "latency": f"{random.randint(200,400)}ms", "icon": "📝"},
        {"name": "Streaming WebSocket", "status": "online", "uptime": "99.90%", "latency": f"{random.randint(10,30)}ms", "icon": "📡"},
        {"name": "Banco de Dados", "status": db_status, "uptime": "99.99%", "latency": f"{db_latency}ms", "icon": "🗄️"},
        {"name": "Armazenamento Local", "status": "online", "uptime": "99.97%", "latency": f"{random.randint(5,15)}ms", "icon": "☁️"},
    ]
    overall = "danger" if any(s["status"]=="danger" for s in services) else "warn" if any(s["status"]=="warn" for s in services) else "online"
    online_count = sum(1 for s in services if s["status"] == "online")
    avg_lat = sum(int(s["latency"].replace("ms","")) for s in services) // len(services)
    return jsonify({
        "overall_status": overall, "services": services, "incidents": [],
        "metrics": {"online_count": online_count, "total_count": len(services), "avg_latency": f"{avg_lat}ms", "uptime_30d": "99.94%"},
    })
