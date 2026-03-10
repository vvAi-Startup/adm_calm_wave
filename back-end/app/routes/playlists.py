from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.supabase_ext import supabase
import json

playlists_bp = Blueprint("playlists", __name__)


def _playlist_with_count(p):
    count = supabase.table('audios').select('id', count='exact').eq('playlist_id', p['id']).execute().count or 0
    p['total_audios'] = count
    return p


@playlists_bp.route("/", methods=["GET"])
@jwt_required()
def list_playlists():
    current_user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page

    resp = supabase.table('playlists').select('*', count='exact').eq('user_id', current_user_id).order('order', desc=False).range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    playlists = [_playlist_with_count(p) for p in (resp.data or [])]

    return jsonify({
        "playlists": playlists,
        "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
        "page": page,
    })


@playlists_bp.route("/", methods=["POST"])
@jwt_required()
def create_playlist():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Nome da playlist e obrigatorio"}), 400

    last = supabase.table('playlists').select('order').eq('user_id', current_user_id).order('order', desc=True).limit(1).execute()
    next_order = (last.data[0]['order'] + 1) if last.data else 0

    resp = supabase.table('playlists').insert({
        "user_id": current_user_id,
        "name": data["name"],
        "color": data.get("color", "#6FAF9E"),
        "order": next_order,
    }).execute()
    playlist = _playlist_with_count(resp.data[0])

    supabase.table('events').insert({
        "user_id": current_user_id,
        "event_type": "PLAYLIST_CREATED",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"playlist_name": data["name"]}),
    }).execute()
    return jsonify({"playlist": playlist}), 201


@playlists_bp.route("/<int:playlist_id>", methods=["GET"])
@jwt_required()
def get_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('playlists').select('*').eq('id', playlist_id).eq('user_id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    playlist = _playlist_with_count(resp.data[0])
    playlist["audios"] = supabase.table('audios').select('*').eq('playlist_id', playlist_id).execute().data or []
    return jsonify({"playlist": playlist})


@playlists_bp.route("/<int:playlist_id>", methods=["PUT"])
@jwt_required()
def update_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('playlists').select('*').eq('id', playlist_id).eq('user_id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    old = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in ['name', 'color', 'order']:
        if field in data and old.get(field) != data[field]:
            changes[field] = {"old": old.get(field), "new": data[field]}
            update_data[field] = data[field]
    if update_data:
        supabase.table('playlists').update(update_data).eq('id', playlist_id).execute()
    if changes:
        supabase.table('events').insert({
            "user_id": current_user_id,
            "event_type": "PLAYLIST_UPDATED",
            "level": "info",
            "screen": "playlists",
            "details_json": json.dumps({"playlist_id": playlist_id, "changes": changes}),
        }).execute()
    updated = supabase.table('playlists').select('*').eq('id', playlist_id).execute().data[0]
    return jsonify({"playlist": _playlist_with_count(updated)})


@playlists_bp.route("/<int:playlist_id>", methods=["DELETE"])
@jwt_required()
def delete_playlist(playlist_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('playlists').select('*').eq('id', playlist_id).eq('user_id', current_user_id).execute()
    if not resp.data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    name = resp.data[0]['name']
    supabase.table('audios').update({"playlist_id": None}).eq('playlist_id', playlist_id).execute()
    supabase.table('playlists').delete().eq('id', playlist_id).execute()
    supabase.table('events').insert({
        "user_id": current_user_id,
        "event_type": "PLAYLIST_DELETED",
        "level": "warn",
        "screen": "playlists",
        "details_json": json.dumps({"playlist_id": playlist_id, "name": name}),
    }).execute()
    return jsonify({"message": "Playlist removida com sucesso"})


@playlists_bp.route("/<int:playlist_id>/add-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def add_audio_to_playlist(playlist_id, audio_id):
    current_user_id = get_jwt_identity()
    if not supabase.table('playlists').select('id').eq('id', playlist_id).eq('user_id', current_user_id).execute().data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    a_resp = supabase.table('audios').select('*').eq('id', audio_id).eq('user_id', current_user_id).execute()
    if not a_resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = a_resp.data[0]
    if audio.get('playlist_id') == playlist_id:
        return jsonify({"error": "Audio ja esta nesta playlist"}), 400
    old_playlist_id = audio.get('playlist_id')
    supabase.table('audios').update({"playlist_id": playlist_id}).eq('id', audio_id).execute()
    supabase.table('events').insert({
        "user_id": current_user_id,
        "event_type": "AUDIO_ADDED_TO_PLAYLIST",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"audio_id": audio_id, "playlist_id": playlist_id, "old_playlist_id": old_playlist_id}),
    }).execute()
    updated = supabase.table('audios').select('*').eq('id', audio_id).execute().data[0]
    return jsonify({"audio": updated})


@playlists_bp.route("/<int:playlist_id>/remove-audio/<int:audio_id>", methods=["POST"])
@jwt_required()
def remove_audio_from_playlist(playlist_id, audio_id):
    current_user_id = get_jwt_identity()
    if not supabase.table('playlists').select('id').eq('id', playlist_id).eq('user_id', current_user_id).execute().data:
        return jsonify({"error": "Playlist nao encontrada"}), 404
    if not supabase.table('audios').select('id').eq('id', audio_id).eq('user_id', current_user_id).eq('playlist_id', playlist_id).execute().data:
        return jsonify({"error": "Audio nao encontrado nesta playlist"}), 404
    supabase.table('audios').update({"playlist_id": None}).eq('id', audio_id).execute()
    supabase.table('events').insert({
        "user_id": current_user_id,
        "event_type": "AUDIO_REMOVED_FROM_PLAYLIST",
        "level": "info",
        "screen": "playlists",
        "details_json": json.dumps({"audio_id": audio_id, "playlist_id": playlist_id}),
    }).execute()
    return jsonify({"message": "Audio removido da playlist"})


@playlists_bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_playlists():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or not isinstance(data.get("playlists"), list):
        return jsonify({"error": "Formato invalido. 'playlists' deve ser uma lista"}), 400
    created_count = updated_count = 0
    for p_data in data["playlists"]:
        name = p_data.get("name")
        if not name:
            continue
        color, order = p_data.get("color", "#6FAF9E"), p_data.get("order", 0)
        existing = supabase.table('playlists').select('id').eq('user_id', current_user_id).eq('name', name).execute()
        if existing.data:
            supabase.table('playlists').update({"color": color, "order": order}).eq('id', existing.data[0]['id']).execute()
            updated_count += 1
        else:
            supabase.table('playlists').insert({"user_id": current_user_id, "name": name, "color": color, "order": order}).execute()
            created_count += 1
    return jsonify({"message": "Sincronizacao concluida", "created": created_count, "updated": updated_count}), 200
