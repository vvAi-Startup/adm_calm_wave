from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.supabase_ext import supabase
import json

events_bp = Blueprint("events", __name__)


@events_bp.route("/", methods=["GET"])
@jwt_required()
def list_events():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    level = request.args.get("level", None)
    offset = (page - 1) * per_page

    query = supabase.table('events').select('*', count='exact').order('created_at', desc=True)
    if level:
        query = query.eq('level', level)
    resp = query.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return jsonify({
        "events": resp.data or [],
        "total": total,
        "pages": pages,
    })


@events_bp.route("/", methods=["POST"])
@jwt_required()
def create_event():
    data = request.get_json()
    event = {
        "user_id": data.get("user_id"),
        "event_type": data.get("event_type", "unknown"),
        "details_json": json.dumps(data.get("details", {})),
        "screen": data.get("screen"),
        "level": data.get("level", "info"),
    }
    resp = supabase.table('events').insert(event).execute()
    return jsonify({"event": resp.data[0]}), 201
