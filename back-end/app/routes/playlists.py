from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.other import Playlist
from app.models.user import User
from app.models.audio import Audio
from app.models.other import Event
from datetime import datetime
import json

playlists_bp = Blueprint("playlists", __name__)


@playlists_bp.route("/", methods=["GET"])
@jwt_required()
def list_playlists():
    """List all playlists of the current user"""
    current_user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = Playlist.query.filter_by(user_id=current_user_id).order_by(
        Playlist.order.asc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "playlists": [p.to_dict() for p in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
        }
    )


@playlists_bp.route("/", methods=["POST"])
@jwt_required()
def create_playlist():
    """Create a new playlist"""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or "name" not in data:
        return jsonify({"error": "Nome da playlist é obrigatório"}), 400

    # Get the next order value
    last_playlist = (
        Playlist.query.filter_by(user_id=current_user_id)
        .order_by(Playlist.order.desc())
        .first()
    )
    next_order = (last_playlist.order + 1) if last_playlist else 0

    playlist = Playlist(
        user_id=current_user_id,
        name=data["name"],
        color=data.get("color", "#6FAF9E"),
        order=next_order,
    )
    db.session.add(playlist)

    # Log event
    create_event = Event(
        user_id=current_user_id,
        event_type="PLAYLIST_CREATED",
        level="info",
        screen="playlists",
        details_json=json.dumps({"playlist_name": data["name"]}),
    )
    db.session.add(create_event)
    db.session.commit()

    return jsonify({"playlist": playlist.to_dict()}), 201


@playlists_bp.route("/<int:playlist_id>", methods=["GET"])
@jwt_required()
def get_playlist(playlist_id):
    """Get a specific playlist with its audios"""
    current_user_id = get_jwt_identity()
    playlist = Playlist.query.filter_by(
        id=playlist_id, user_id=current_user_id
    ).first_or_404()

    playlist_data = playlist.to_dict()
    # Get audios in this playlist
    audios = Audio.query.filter_by(playlist_id=playlist_id).all()
    playlist_data["audios"] = [a.to_dict() for a in audios]

    return jsonify({"playlist": playlist_data})


@playlists_bp.route("/<int:playlist_id>", methods=["PUT"])
@jwt_required()
def update_playlist(playlist_id):
    """Update a playlist"""
    current_user_id = get_jwt_identity()
    playlist = Playlist.query.filter_by(
        id=playlist_id, user_id=current_user_id
    ).first_or_404()
    data = request.get_json()

    changes = {}
    if "name" in data and playlist.name != data["name"]:
        changes["name"] = {"old": playlist.name, "new": data["name"]}
        playlist.name = data["name"]

    if "color" in data and playlist.color != data["color"]:
        changes["color"] = {"old": playlist.color, "new": data["color"]}
        playlist.color = data["color"]

    if "order" in data and playlist.order != data["order"]:
        changes["order"] = {"old": playlist.order, "new": data["order"]}
        playlist.order = data["order"]

    if changes:
        update_event = Event(
            user_id=current_user_id,
            event_type="PLAYLIST_UPDATED",
            level="info",
            screen="playlists",
            details_json=json.dumps({"playlist_id": playlist_id, "changes": changes}),
        )
        db.session.add(update_event)

    db.session.commit()
    return jsonify({"playlist": playlist.to_dict()})


@playlists_bp.route("/<int:playlist_id>", methods=["DELETE"])
@jwt_required()
def delete_playlist(playlist_id):
    """Delete a playlist"""
    current_user_id = get_jwt_identity()
    playlist = Playlist.query.filter_by(
        id=playlist_id, user_id=current_user_id
    ).first_or_404()

    # Remove all audios from this playlist
    Audio.query.filter_by(playlist_id=playlist_id).update({"playlist_id": None})

    db.session.delete(playlist)

    # Log event
    delete_event = Event(
        user_id=current_user_id,
        event_type="PLAYLIST_DELETED",
        level="warn",
        screen="playlists",
        details_json=json.dumps({"playlist_id": playlist_id, "name": playlist.name}),
    )
    db.session.add(delete_event)
    db.session.commit()

    return jsonify({"message": "Playlist removida com sucesso"})


@playlists_bp.route("/<int:playlist_id>/add-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def add_audio_to_playlist(playlist_id, audio_id):
    """Add an audio to a playlist"""
    current_user_id = get_jwt_identity()
    playlist = Playlist.query.filter_by(
        id=playlist_id, user_id=current_user_id
    ).first_or_404()
    audio = Audio.query.filter_by(id=audio_id, user_id=current_user_id).first_or_404()

    if audio.playlist_id == playlist_id:
        return jsonify({"error": "Áudio já está nesta playlist"}), 400

    # Remove from old playlist if necessary
    old_playlist_id = audio.playlist_id
    audio.playlist_id = playlist_id
    db.session.commit()

    # Log event
    add_event = Event(
        user_id=current_user_id,
        event_type="AUDIO_ADDED_TO_PLAYLIST",
        level="info",
        screen="playlists",
        details_json=json.dumps(
            {
                "audio_id": audio_id,
                "playlist_id": playlist_id,
                "old_playlist_id": old_playlist_id,
            }
        ),
    )
    db.session.add(add_event)
    db.session.commit()

    return jsonify({"audio": audio.to_dict()})


@playlists_bp.route("/<int:playlist_id>/remove-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def remove_audio_from_playlist(playlist_id, audio_id):
    """Remove an audio from a playlist"""
    current_user_id = get_jwt_identity()
    playlist = Playlist.query.filter_by(
        id=playlist_id, user_id=current_user_id
    ).first_or_404()
    audio = Audio.query.filter_by(
        id=audio_id, user_id=current_user_id, playlist_id=playlist_id
    ).first_or_404()

    audio.playlist_id = None
    db.session.commit()

    # Log event
    remove_event = Event(
        user_id=current_user_id,
        event_type="AUDIO_REMOVED_FROM_PLAYLIST",
        level="info",
        screen="playlists",
        details_json=json.dumps({"audio_id": audio_id, "playlist_id": playlist_id}),
    )
    db.session.add(remove_event)
    db.session.commit()

    return jsonify({"message": "Áudio removido da playlist"})

@playlists_bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_playlists():
    """Sincroniza playlists criadas offline no mobile"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not isinstance(data.get("playlists"), list):
        return jsonify({"error": "Formato inválido. 'playlists' deve ser uma lista"}), 400
        
    created_count = 0
    updated_count = 0
    
    for p_data in data["playlists"]:
        name = p_data.get("name")
        if not name:
            continue
            
        color = p_data.get("color", "#6FAF9E")
        order = p_data.get("order", 0)
        
        existing = Playlist.query.filter_by(user_id=current_user_id, name=name).first()
        
        if existing:
            existing.color = color
            existing.order = order
            updated_count += 1
        else:
            new_playlist = Playlist(
                user_id=current_user_id,
                name=name,
                color=color,
                order=order
            )
            db.session.add(new_playlist)
            created_count += 1
            
    db.session.commit()
    
    return jsonify({
        "message": "Sincronização concluída",
        "created": created_count,
        "updated": updated_count
    }), 200
