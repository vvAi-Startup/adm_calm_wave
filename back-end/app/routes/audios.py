from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from app.supabase_ext import supabase
import os, time, io, zipfile, json, threading
from werkzeug.utils import secure_filename
from app.services.push_service import PushService

audios_bp = Blueprint("audios", __name__)

try:
    from app.services.audio_processor import denoiser, transcribe_audio, get_audio_duration
except ImportError:
    denoiser = None
    transcribe_audio = None
    get_audio_duration = lambda p: 0.0
    print("Warning: Audio processor not available")


@audios_bp.route("/play/<int:audio_id>", methods=["GET"])
def play_audio(audio_id):
    resp = supabase.table('audios').select('file_path,processed_path,processed').eq('id', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = resp.data[0]
    audio_type = request.args.get("type", "processed")
    if audio_type == "original":
        file_path = audio.get('file_path')
    else:
        file_path = audio.get('processed_path') if audio.get('processed') and audio.get('processed_path') else audio.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo de audio nao encontrado"}), 404
    response = send_file(file_path, mimetype="audio/wav", conditional=True)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@audios_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome de arquivo vazio"}), 400
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".aac")):
        return jsonify({"error": "Formato nao suportado."}), 400

    user_id = get_jwt_identity()
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Calcular duração real do áudio
    duration_sec = int(get_audio_duration(file_path))

    audio_resp = supabase.table('audios').insert({
        "user_id": int(user_id),
        "filename": filename,
        "file_path": file_path,
        "size_bytes": os.path.getsize(file_path),
        "duration_seconds": duration_sec,
        "device_origin": request.form.get("device_origin", "Web"),
        "processed": False,
        "transcribed": False,
        "favorite": False,
    }).execute()
    audio = audio_resp.data[0]

    # Log de evento + processamento em background (não bloqueia a resposta)
    _enqueue_processing(audio['id'], file_path, user_id, event_log={
        "user_id": int(user_id), "filename": filename, "size": audio['size_bytes']
    })

    return jsonify({"audio": audio}), 201


def _enqueue_processing(audio_id, file_path, user_id, event_log=None):
    """Processa o áudio e registra o evento em background usando thread."""
    from app.tasks.audio_tasks import _do_process

    def _run():
        if event_log:
            try:
                supabase.table('events').insert({
                    "user_id": event_log["user_id"], "event_type": "AUDIO_UPLOADED",
                    "level": "info", "screen": "audio",
                    "details_json": json.dumps({"filename": event_log["filename"], "size": event_log["size"]}),
                }).execute()
            except Exception:
                pass
        _do_process(audio_id, file_path, user_id)

    threading.Thread(target=_run, daemon=True).start()


@audios_bp.route("/sync", methods=["POST"])
@jwt_required()
def sync_audio_offline():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo original enviado"}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg", ".aac")):
        return jsonify({"error": "Arquivo invalido"}), 400
    user_id = get_jwt_identity()
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, "sync_" + filename)
    file.save(file_path)
    processed_path, processed = None, False
    if 'processed_file' in request.files:
        pf = request.files['processed_file']
        if pf.filename != '':
            pn = "processed_sync_" + secure_filename(pf.filename)
            processed_path = os.path.join(upload_dir, pn)
            pf.save(processed_path)
            processed = True
    transcription = request.form.get("transcription_text", "")
    resp = supabase.table('audios').insert({
        "user_id": user_id, "filename": filename, "file_path": file_path,
        "size_bytes": os.path.getsize(file_path),
        "duration_seconds": request.form.get("duration_seconds", 0, type=int),
        "device_origin": request.form.get("device_origin", "Mobile App (Offline Sync)"),
        "processed": processed, "processed_path": processed_path,
        "processing_time_ms": request.form.get("processing_time_ms", 0, type=int),
        "transcribed": bool(transcription),
        "transcription_text": transcription if transcription else None,
        "favorite": False,
    }).execute()
    audio = resp.data[0]
    supabase.table('events').insert({
        "user_id": user_id, "event_type": "AUDIO_SYNCED_OFFLINE", "level": "info",
        "screen": "audio_sync",
        "details_json": json.dumps({"filename": filename, "processed": processed, "transcribed": bool(transcription)}),
    }).execute()
    return jsonify({"audio": audio, "message": "Audio sincronizado com sucesso (Offline Sync)"}), 201


@audios_bp.route("/<int:audio_id>/reprocess", methods=["POST"])
@jwt_required()
def reprocess_audio(audio_id):
    """Reprocessa um áudio que ficou com status Pendente."""
    current_user_id = get_jwt_identity()
    resp = supabase.table('audios').select('*').eq('id', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Áudio não encontrado"}), 404
    audio = resp.data[0]
    file_path = audio.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo de áudio não encontrado no servidor"}), 404
    # Limpar erro anterior e resetar status
    supabase.table('audios').update({
        "processed": False, "processing_error": None
    }).eq('id', audio_id).execute()
    _enqueue_processing(audio_id, file_path, current_user_id)
    return jsonify({"message": "Reprocessamento enfileirado", "audio_id": audio_id}), 202


@audios_bp.route("/", methods=["GET"])
@jwt_required()
def list_audios():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    processed = request.args.get("processed", None)
    favorite = request.args.get("favorite", None)
    offset = (page - 1) * per_page
    q = supabase.table('audios').select('*', count='exact').order('recorded_at', desc=True)
    if processed is not None:
        q = q.eq('processed', processed == "true")
    if favorite is not None:
        q = q.eq('favorite', favorite == "true")
    resp = q.range(offset, offset + per_page - 1).execute()
    total = resp.count or 0
    return jsonify({
        "audios": resp.data or [], "total": total,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1, "page": page,
    })


@audios_bp.route("/", methods=["POST"])
@jwt_required()
def create_audio():
    data = request.get_json()
    resp = supabase.table('audios').insert({
        "user_id": data["user_id"], "filename": data["filename"],
        "file_path": data.get("file_path"),
        "duration_seconds": data.get("duration_seconds", 0),
        "size_bytes": data.get("size_bytes", 0),
        "device_origin": data.get("device_origin"),
        "processed": False, "transcribed": False, "favorite": False,
    }).execute()
    return jsonify({"audio": resp.data[0]}), 201


@audios_bp.route("/<int:audio_id>", methods=["GET"])
@jwt_required()
def get_audio(audio_id):
    resp = supabase.table('audios').select('*').eq('id', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    return jsonify({"audio": resp.data[0]})


@audios_bp.route("/<int:audio_id>", methods=["PUT"])
@jwt_required()
def update_audio(audio_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('audios').select('*').eq('id', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    audio = resp.data[0]
    data = request.get_json()
    changes, update_data = {}, {}
    for field in ["processed", "transcribed", "favorite", "transcription_text", "playlist_id"]:
        if field in data:
            old_val = audio.get(field)
            new_val = data[field]
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
            update_data[field] = new_val
    if update_data:
        supabase.table('audios').update(update_data).eq('id', audio_id).execute()
    if changes:
        supabase.table('events').insert({
            "user_id": current_user_id, "event_type": "AUDIO_UPDATED", "level": "info",
            "screen": "audios", "details_json": json.dumps({"audio_id": audio_id, "changes": changes}),
        }).execute()
    updated = supabase.table('audios').select('*').eq('id', audio_id).execute().data[0]
    return jsonify({"audio": updated})


@audios_bp.route("/<int:audio_id>", methods=["DELETE"])
@jwt_required()
def delete_audio(audio_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table('audios').select('filename').eq('id', audio_id).execute()
    if not resp.data:
        return jsonify({"error": "Audio nao encontrado"}), 404
    filename = resp.data[0]['filename']
    supabase.table('events').insert({
        "user_id": current_user_id, "event_type": "AUDIO_DELETED", "level": "warn",
        "screen": "audios", "details_json": json.dumps({"audio_id": audio_id, "filename": filename}),
    }).execute()
    supabase.table('audios').delete().eq('id', audio_id).execute()
    return jsonify({"message": "Audio removido com sucesso"})


@audios_bp.route("/batch-export", methods=["POST"])
@jwt_required()
def batch_export_audios():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    audio_ids = data.get("audio_ids", [])
    if not audio_ids:
        return jsonify({"error": "Nenhum audio selecionado"}), 400
    audios = supabase.table('audios').select('*').in_('id', audio_ids).eq('user_id', current_user_id).execute().data or []
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for audio in audios:
            fzip = audio.get('processed_path') if (audio.get('processed') and audio.get('processed_path')) else audio.get('file_path')
            if fzip and os.path.exists(fzip):
                zf.write(fzip, arcname=f"audios/{audio['filename']}")
            if audio.get('transcription_text'):
                txt_name = f"transcriptions/{os.path.splitext(audio['filename'])[0]}.txt"
                zf.writestr(txt_name, audio['transcription_text'])
    memory_file.seek(0)
    return send_file(memory_file, mimetype="application/zip", as_attachment=True, download_name="calmwave_export.zip")
