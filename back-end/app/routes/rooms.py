from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from app import socketio
from app.supabase_ext import supabase
import time
import random
import string
import os
import base64
import json
from datetime import datetime
from tempfile import NamedTemporaryFile

from app.services.cloudinary_service import upload_audio_bytes

rooms_bp = Blueprint("rooms", __name__)

try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None

# room_code -> {file_path, filename, host_sid, start_time, messages}
active_room_streams = {}


def _generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _get_valid_user_id():
    try:
        resp = supabase.table('users').select('id').order('id').limit(1).execute()
        if resp.data:
            return resp.data[0]['id']
    except Exception:
        pass
    return 1


# ─── REST ─────────────────────────────────────────────────────────────────────

@rooms_bp.route("", methods=["POST"])
def create_room():
    data = request.get_json() or {}
    name = data.get("name", "Minha Sala")
    host_user_id = data.get("host_user_id")

    room_code = _generate_room_code()
    # Garantir unicidade
    for _ in range(5):
        existing = supabase.table('rooms').select('id').eq('room_code', room_code).execute()
        if not existing.data:
            break
        room_code = _generate_room_code()

    resp = supabase.table('rooms').insert({
        "name": name,
        "host_user_id": host_user_id,
        "room_code": room_code,
        "is_active": True,
    }).execute()

    if not resp.data:
        return jsonify({"error": "Falha ao criar sala"}), 500

    return jsonify({"room": resp.data[0]}), 201


@rooms_bp.route("", methods=["GET"])
def list_rooms():
    resp = supabase.table('rooms').select('*').eq('is_active', True).order('created_at', desc=True).execute()
    return jsonify({"rooms": resp.data or []})


@rooms_bp.route("/<room_code>", methods=["GET"])
def get_room(room_code):
    room_resp = supabase.table('rooms').select('*').eq('room_code', room_code).execute()
    if not room_resp.data:
        return jsonify({"error": "Sala não encontrada"}), 404

    room = room_resp.data[0]
    parts_resp = supabase.table('room_participants') \
        .select('*') \
        .eq('room_id', room['id']) \
        .is_('left_at', 'null') \
        .execute()

    return jsonify({"room": room, "participants": parts_resp.data or []})


@rooms_bp.route("/<room_code>", methods=["DELETE"])
def close_room(room_code):
    room_resp = supabase.table('rooms').select('id').eq('room_code', room_code).execute()
    if not room_resp.data:
        return jsonify({"error": "Sala não encontrada"}), 404

    supabase.table('rooms').update({"is_active": False}).eq('room_code', room_code).execute()
    socketio.emit('room_closed', {"room_code": room_code}, to=f"room_{room_code}")
    return jsonify({"message": "Sala encerrada"})


# ─── WebSocket ────────────────────────────────────────────────────────────────

@socketio.on('join_room_as_host')
def handle_join_as_host(data):
    """Host se conecta à sala e fica pronto para transmitir."""
    sid = request.sid
    room_code = data.get('room_code')
    username = data.get('user', 'Host')
    device = data.get('device', 'Unknown')

    if not room_code:
        emit('room_error', {'message': 'room_code obrigatório'})
        return

    room_resp = supabase.table('rooms').select('*').eq('room_code', room_code).eq('is_active', True).execute()
    if not room_resp.data:
        emit('room_error', {'message': 'Sala não encontrada ou inativa'})
        return

    room = room_resp.data[0]
    join_room(f"room_{room_code}")

    # Registra participante host
    supabase.table('room_participants').insert({
        "room_id": room['id'],
        "socket_id": sid,
        "role": "host",
        "username": username,
    }).execute()

    # Cria arquivo para gravar o stream
    upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"room_{room_code}_{int(time.time())}.wav"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb'):
        pass

    active_room_streams[room_code] = {
        "host_sid": sid,
        "file_path": file_path,
        "filename": filename,
        "device": device,
        "start_time": time.time(),
        "messages": 0,
        "room_id": room['id'],
    }

    emit('room_joined', {
        'room_code': room_code,
        'room_name': room['name'],
        'role': 'host',
    })

    socketio.emit('room_participant_joined', {
        'room_code': room_code,
        'username': username,
        'role': 'host',
        'socket_id': sid,
    }, to=f"room_{room_code}")


@socketio.on('join_room_as_listener')
def handle_join_as_listener(data):
    """Listener entra na sala pelo código para receber o áudio."""
    sid = request.sid
    room_code = data.get('room_code')
    username = data.get('user', 'Ouvinte')

    if not room_code:
        emit('room_error', {'message': 'room_code obrigatório'})
        return

    room_resp = supabase.table('rooms').select('*').eq('room_code', room_code).eq('is_active', True).execute()
    if not room_resp.data:
        emit('room_error', {'message': 'Sala não encontrada ou inativa'})
        return

    room = room_resp.data[0]
    join_room(f"room_{room_code}")

    supabase.table('room_participants').insert({
        "room_id": room['id'],
        "socket_id": sid,
        "role": "listener",
        "username": username,
    }).execute()

    # Busca participantes ativos na sala
    parts_resp = supabase.table('room_participants') \
        .select('username, role') \
        .eq('room_id', room['id']) \
        .is_('left_at', 'null') \
        .execute()

    emit('room_joined', {
        'room_code': room_code,
        'room_name': room['name'],
        'role': 'listener',
        'participants': parts_resp.data or [],
    })

    socketio.emit('room_participant_joined', {
        'room_code': room_code,
        'username': username,
        'role': 'listener',
        'socket_id': sid,
    }, to=f"room_{room_code}", skip_sid=sid)


@socketio.on('leave_room_session')
def handle_leave_room(data):
    """Usuário sai da sala."""
    sid = request.sid
    room_code = data.get('room_code')
    if not room_code:
        return

    leave_room(f"room_{room_code}")

    supabase.table('room_participants') \
        .update({"left_at": datetime.utcnow().isoformat()}) \
        .eq('socket_id', sid) \
        .is_('left_at', 'null') \
        .execute()

    socketio.emit('room_participant_left', {
        'room_code': room_code,
        'socket_id': sid,
    }, to=f"room_{room_code}")


@socketio.on('disconnect')
def handle_room_disconnect():
    sid = request.sid
    try:
        supabase.table('room_participants') \
            .update({"left_at": datetime.utcnow().isoformat()}) \
            .eq('socket_id', sid) \
            .is_('left_at', 'null') \
            .execute()
    except Exception as e:
        print(f"Erro ao atualizar desconexão do socket {sid}: {e}")

    disconnected_rooms = [
        room_code for room_code, stream in active_room_streams.items()
        if stream.get("host_sid") == sid
    ]
    for room_code in disconnected_rooms:
        stream = active_room_streams.pop(room_code, None)
        if not stream:
            continue
        try:
            if os.path.exists(stream["file_path"]):
                os.remove(stream["file_path"])
        except Exception as e:
            print(f"Erro ao limpar stream da sala {room_code}: {e}")


@socketio.on('audio_chunk_room')
def handle_audio_chunk_room(data):
    """
    Host envia chunk de áudio.
    O servidor salva no arquivo local E retransmite em tempo real para os listeners da sala.
    """
    sid = request.sid
    room_code = data.get('room_code')

    if not room_code or room_code not in active_room_streams:
        return {"status": "error", "message": "Stream não iniciado"}

    stream = active_room_streams[room_code]
    if stream["host_sid"] != sid:
        return {"status": "error", "message": "Apenas o host pode transmitir áudio"}

    audio_data = data.get("audio_data")
    if audio_data:
        try:
            audio_bytes = base64.b64decode(audio_data)
            with open(stream["file_path"], 'ab') as f:
                f.write(audio_bytes)
        except Exception as e:
            print(f"Erro ao salvar chunk da sala {room_code}: {e}")

    stream["messages"] += 1

    # Retransmite o chunk bruto para todos os listeners da sala (exceto o host)
    socketio.emit('room_audio_chunk', {
        'room_code': room_code,
        'audio_data': audio_data,
        'chunk_index': stream["messages"],
    }, to=f"room_{room_code}", skip_sid=sid)

    return {"status": "ok", "chunk_index": stream["messages"]}


@socketio.on('stop_room_stream')
def handle_stop_room_stream(data):
    """
    Host encerra o stream. O servidor processa o áudio completo
    (denoise + transcrição) e notifica toda a sala.
    """
    sid = request.sid
    room_code = data.get('room_code')

    if not room_code or room_code not in active_room_streams:
        emit('room_error', {'message': 'Nenhum stream ativo para esta sala'})
        return

    stream = active_room_streams[room_code]
    if stream["host_sid"] != sid:
        emit('room_error', {'message': 'Apenas o host pode encerrar o stream'})
        return

    file_path = stream["file_path"]
    filename = stream["filename"]
    device = stream["device"]
    duration = int(time.time() - stream["start_time"])

    try:
        user_id = _get_valid_user_id()
        size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        if size_bytes > 0:
            with open(file_path, 'rb') as f:
                raw_audio_bytes = f.read()

            original_upload = upload_audio_bytes(
                raw_audio_bytes,
                filename=filename,
                folder="calmwave/audios/original",
            )

            audio_resp = supabase.table('audios').insert({
                "user_id": user_id,
                "filename": filename,
                "file_path": original_upload["secure_url"],
                "size_bytes": size_bytes,
                "duration_seconds": duration,
                "device_origin": f"{device} (Sala {room_code})",
                "processed": False,
                "transcribed": False,
                "favorite": False,
            }).execute()

            audio = audio_resp.data[0]

            # Notifica sala que o processamento começou
            socketio.emit('room_stream_processing', {
                'room_code': room_code,
                'message': 'Áudio recebido. Processando com IA...',
            }, to=f"room_{room_code}")

            if denoiser and denoiser.ensure_model_loaded():
                try:
                    processed_bytes = denoiser.denoise_audio(raw_audio_bytes)
                    pname = f"processed_{filename}"
                    processed_upload = upload_audio_bytes(
                        processed_bytes,
                        filename=pname,
                        folder="calmwave/audios/processed",
                    )
                    ppath = processed_upload["secure_url"]
                    update_data = {
                        "processed": True,
                        "processed_path": ppath,
                    }

                    transcription = None
                    if transcribe_audio:
                        with NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                            tmp.write(processed_bytes)
                            tmp_path = tmp.name
                        try:
                            transcription = transcribe_audio(tmp_path, language='pt-BR')
                        finally:
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                        if transcription:
                            update_data["transcribed"] = True
                            update_data["transcription_text"] = transcription

                    supabase.table('audios').update(update_data).eq('id', audio['id']).execute()

                    # Notifica toda a sala com o resultado processado
                    socketio.emit('room_audio_completed', {
                        'room_code': room_code,
                        'audio_id': audio['id'],
                        'processed_url': ppath,
                        'transcription': transcription,
                        'duration_seconds': duration,
                        'filename': filename,
                    }, to=f"room_{room_code}")

                except Exception as e:
                    print(f"Erro no processamento da sala {room_code}: {e}")
                    socketio.emit('room_audio_completed', {
                        'room_code': room_code,
                        'audio_id': audio['id'],
                        'processed_url': None,
                        'transcription': None,
                        'duration_seconds': duration,
                        'filename': filename,
                    }, to=f"room_{room_code}")
            else:
                socketio.emit('room_audio_completed', {
                    'room_code': room_code,
                    'audio_id': audio['id'],
                    'processed_url': None,
                    'transcription': None,
                    'duration_seconds': duration,
                    'filename': filename,
                }, to=f"room_{room_code}")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    except Exception as e:
        print(f"Erro ao encerrar stream da sala {room_code}: {e}")
        socketio.emit('room_error', {
            'room_code': room_code,
            'message': 'Erro ao processar o áudio',
        }, to=f"room_{room_code}")
    finally:
        active_room_streams.pop(room_code, None)

    return {"status": "ok"}
