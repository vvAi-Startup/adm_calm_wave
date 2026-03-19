from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.supabase_ext import supabase
import time
from datetime import datetime
import os, base64, json

streaming_bp = Blueprint("streaming", __name__)

try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None
    print("Warning: Audio processor not available")

active_sessions = {}

def _get_valid_user_id():
    try:
        resp = supabase.table('users').select('id').order('id').limit(1).execute()
        if resp.data:
            return resp.data[0]['id']
    except Exception:
        pass
    return 1

@streaming_bp.route("/sessions", methods=["GET"])
def get_sessions():
    sessions_list = []
    for sid, data in active_sessions.items():
        duration_seconds = int(time.time() - data["start_time"])
        m, s = divmod(duration_seconds, 60)
        sessions_list.append({
            "id": sid, "user": data.get("user", "Anonymous"),
            "device": data.get("device", "Unknown"),
            "connected_at": data["connected_at"],
            "duration": f"{m}m {s}s",
            "messages": data.get("messages", 0),
            "status": "online",
        })
    return jsonify({"sessions": sessions_list})


@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in active_sessions:
        del active_sessions[request.sid]
        socketio.emit('session_update', {'action': 'remove', 'id': request.sid})


@socketio.on('start_stream')
def handle_start_stream(data):
    sid = request.sid
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"stream_{sid}_{int(time.time())}.wav"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb') as f:
        pass
    active_sessions[sid] = {
        "id": sid, "user": data.get("user", "Anonymous"), "device": data.get("device", "Unknown"),
        "start_time": time.time(), "connected_at": datetime.utcnow().isoformat() + "Z",
        "messages": 0, "file_path": file_path, "filename": filename,
    }
    try:
        uid = _get_valid_user_id()
        supabase.table('events').insert({
            "user_id": uid, "event_type": "STREAMING_START", "level": "info", "screen": "streaming",
            "details_json": json.dumps({"session_id": sid, "device": data.get("device", "Unknown")}),
        }).execute()
    except Exception as e:
        print(f"Error logging stream start: {e}")
    socketio.emit('session_update', {'action': 'add', 'session': active_sessions[sid], 'id': sid})
    return {"status": "ok", "message": "Stream started"}


@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid]["messages"] += 1
        if "audio_data" in data:
            try:
                audio_bytes = base64.b64decode(data["audio_data"])
                with open(active_sessions[sid]["file_path"], 'ab') as f:
                    f.write(audio_bytes)
            except Exception as e:
                print(f"Error saving audio chunk: {e}")
        if active_sessions[sid]["messages"] % 5 == 0:
            socketio.emit('session_stats', {
                'id': sid, 'messages': active_sessions[sid]["messages"],
                'active_sessions': len(active_sessions),
                'messages_per_min': sum(s.get("messages", 0) for s in active_sessions.values()) * 2,
                'latency_ms': 12, 'bandwidth_mbps': round(len(active_sessions) * 0.5, 1),
            })
    return {"status": "ok"}


@socketio.on('stop_stream')
def handle_stop_stream():
    sid = request.sid
    if sid in active_sessions:
        session_data = active_sessions[sid]
        try:
            user_id = _get_valid_user_id()
            file_path = session_data["file_path"]
            size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            duration = int(time.time() - session_data["start_time"])
            if size_bytes > 0:
                audio_resp = supabase.table('audios').insert({
                    "user_id": user_id, "filename": session_data["filename"],
                    "file_path": file_path, "size_bytes": size_bytes,
                    "duration_seconds": duration,
                    "device_origin": session_data["device"] + " (Stream)",
                    "processed": False, "transcribed": False, "favorite": False,
                }).execute()
                audio = audio_resp.data[0]
                supabase.table('events').insert({
                    "user_id": user_id, "event_type": "STREAMING_STOP", "level": "info", "screen": "streaming",
                    "details_json": json.dumps({
                        "session_id": sid, "duration_seconds": duration,
                        "size_bytes": size_bytes, "audio_id": audio.get('id'),
                    }),
                }).execute()
                if denoiser and denoiser.ensure_model_loaded():
                    try:
                        start_p = time.time()
                        with open(file_path, 'rb') as f:
                            raw = f.read()
                        processed_bytes = denoiser.denoise_audio(raw)
                        pname = f"processed_{session_data['filename']}"
                        ppath = os.path.join(os.path.dirname(file_path), pname)
                        with open(ppath, 'wb') as f:
                            f.write(processed_bytes)
                        update_data = {
                            "processed": True, "processed_path": ppath,
                            "processing_time_ms": int((time.time() - start_p) * 1000),
                        }
                        if transcribe_audio:
                            lang = 'pt-BR'
                            tx = transcribe_audio(ppath, language=lang)
                            if tx:
                                update_data["transcribed"] = True
                                update_data["transcription_text"] = tx
                        supabase.table('audios').update(update_data).eq('id', audio['id']).execute()
                        notif = supabase.table('notifications').insert({
                            "user_id": user_id,
                            "title": "Audio Processado pela IA",
                            "message": f"A transmissao ao vivo do dispositivo {session_data['device']} foi processada.",
                            "type": "success", "is_read": False,
                        }).execute()
                        socketio.emit('new_notification', notif.data[0])
                    except Exception as e:
                        print(f"Error processing streamed audio: {e}")
        except Exception as e:
            print(f"Error saving stream: {e}")
        del active_sessions[sid]
        socketio.emit('session_update', {'action': 'remove', 'id': sid})
    return {"status": "ok"}
