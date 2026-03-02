from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.other import Event

events_bp = Blueprint("events", __name__)


@events_bp.route("/", methods=["GET"])
@jwt_required()
def list_events():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    level = request.args.get("level", None)

    query = Event.query
    if level:
        query = query.filter(Event.level == level)

    pagination = query.order_by(Event.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify(
        {
            "events": [e.to_dict() for e in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@events_bp.route("/", methods=["POST"])
@jwt_required()
def create_event():
    data = request.get_json()
    import json

    event = Event(
        user_id=data.get("user_id"),
        event_type=data.get("event_type", "unknown"),
        details_json=json.dumps(data.get("details", {})),
        screen=data.get("screen"),
        level=data.get("level", "info"),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({"event": event.to_dict()}), 201
