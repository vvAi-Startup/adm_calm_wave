from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models.audio import Audio
from app.models.other import Event
import time
from datetime import datetime
import os
import base64
import json

streaming_bp = Blueprint("streaming", __name__)

# Import the denoiser
try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None
    print("Warning: Audio processor not available")

# Store active sessions in memory
active_sessions = {}

@streaming_bp.route("/sessions", methods=["GET"])
def get_sessions():
    """Return list of active streaming sessions for the dashboard"""
    sessions_list = []
    for sid, data in active_sessions.items():
        duration_seconds = int(time.time() - data["start_time"])
        m, s = divmod(duration_seconds, 60)
        
        sessions_list.append({
            "id": sid,
            "user": data.get("user", "Anonymous"),
            "device": data.get("device", "Unknown"),
            "connected_at": data["connected_at"],
            "duration": f"{m}m {s}s",
            "messages": data.get("messages", 0),
            "status": "online"
        })
    
    return jsonify({"sessions": sessions_list})

# Socket.IO Event Handlers
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in active_sessions:
        del active_sessions[request.sid]
        # Notify dashboard that a session ended
        socketio.emit('session_update', {'action': 'remove', 'id': request.sid})

@socketio.on('start_stream')
def handle_start_stream(data):
    """Client starts an audio stream"""
    sid = request.sid
    
    # Create a temporary file to store the incoming audio chunks
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"stream_{sid}_{int(time.time())}.wav"
    file_path = os.path.join(upload_dir, filename)
    
    # Create an empty file
    with open(file_path, 'wb') as f:
        pass
        
    active_sessions[sid] = {
        "id": sid,
        "user": data.get("user", "Anonymous"),
        "device": data.get("device", "Unknown"),
        "start_time": time.time(),
        "connected_at": datetime.utcnow().isoformat() + "Z",
        "messages": 0,
        "file_path": file_path,
        "filename": filename
    }
    print(f"Stream started for {sid}: {data}")
    
    # Log event
    try:
        stream_event = Event(
            user_id=1, # Default to admin for now
            event_type="STREAMING_START",
            level="info",
            screen="streaming",
            details_json=json.dumps({"session_id": sid, "device": data.get("device", "Unknown")})
        )
        db.session.add(stream_event)
        db.session.commit()
    except Exception as e:
        print(f"Error logging stream start: {e}")
    
    # Notify dashboard about new session
    socketio.emit('session_update', {'action': 'add', 'session': active_sessions[sid], 'id': sid})
    return {"status": "ok", "message": "Stream started"}

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Receive audio chunk from client"""
    sid = request.sid
    if sid in active_sessions:
        active_sessions[sid]["messages"] += 1
        
        # Append chunk to file if it contains actual audio data
        if "audio_data" in data:
            try:
                # Assuming data is base64 encoded
                audio_bytes = base64.b64decode(data["audio_data"])
                with open(active_sessions[sid]["file_path"], 'ab') as f:
                    f.write(audio_bytes)
            except Exception as e:
                print(f"Error saving audio chunk: {e}")
        
        # Every 5 chunks, update the dashboard
        if active_sessions[sid]["messages"] % 5 == 0:
            socketio.emit('session_stats', {
                'id': sid, 
                'messages': active_sessions[sid]["messages"],
                'active_sessions': len(active_sessions),
                'messages_per_min': sum(s.get("messages", 0) for s in active_sessions.values()) * 2, # Fake calc
                'latency_ms': 12,
                'bandwidth_mbps': round(len(active_sessions) * 0.5, 1)
            })
            
    return {"status": "ok"}

@socketio.on('stop_stream')
def handle_stop_stream():
    """Client stops the stream"""
    sid = request.sid
    if sid in active_sessions:
        print(f"Stream stopped for {sid}")
        session_data = active_sessions[sid]
        
        # Save the completed stream to the database
        try:
            # We need a user_id, default to 1 (admin) for now since we don't have auth in the socket yet
            user_id = 1 
            
            file_path = session_data["file_path"]
            size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            duration = int(time.time() - session_data["start_time"])
            
            # Only save if we actually received some data
            if size_bytes > 0:
                audio = Audio(
                    user_id=user_id,
                    filename=session_data["filename"],
                    file_path=file_path,
                    size_bytes=size_bytes,
                    duration_seconds=duration,
                    device_origin=session_data["device"] + " (Stream)"
                )
                db.session.add(audio)
                
                # Log event
                stop_event = Event(
                    user_id=user_id,
                    event_type="STREAMING_STOP",
                    level="info",
                    screen="streaming",
                    details_json=json.dumps({
                        "session_id": sid, 
                        "duration_seconds": duration,
                        "size_bytes": size_bytes,
                        "audio_id": audio.id if hasattr(audio, 'id') else None
                    })
                )
                db.session.add(stop_event)
                
                db.session.commit()
                print(f"Stream saved to database: {audio.id}")
                
                # Process audio if denoiser is available
                if denoiser and denoiser.model is not None:
                    try:
                        print("Processing streamed audio with IA...")
                        start_processing = time.time()
                        with open(file_path, 'rb') as f:
                            audio_bytes = f.read()

                        # Apply denoising
                        processed_bytes = denoiser.denoise_audio(audio_bytes)

                        processed_filename = f"processed_{session_data['filename']}"
                        upload_dir = os.path.dirname(file_path)
                        processed_path = os.path.join(upload_dir, processed_filename)

                        with open(processed_path, 'wb') as f:
                            f.write(processed_bytes)

                        audio.processed = True
                        audio.processed_path = processed_path
                        audio.processing_time_ms = int((time.time() - start_processing) * 1000)

                        # Transcribe audio
                        if transcribe_audio:
                            print("Transcribing streamed audio...")
                            transcription_text = transcribe_audio(processed_path)
                            if transcription_text:
                                audio.transcribed = True
                                audio.transcription_text = transcription_text
                                print(f"Transcription successful: {transcription_text[:50]}...")
                        
                        db.session.commit()
                        print("Stream IA processing complete.")
                        
                        from app.models.other import Notification
                        notif = Notification(
                            user_id=1,
                            title="Áudio Processado pela IA",
                            message=f"A transmissão ao vivo do dispositivo {session_data['device']} foi salva e processada com sucesso.",
                            type="success"
                        )
                        db.session.add(notif)
                        db.session.commit()
                        
                        # Tell UI real-time
                        socketio.emit('new_notification', notif.to_dict())
                    except Exception as e:
                        print(f"Error processing streamed audio with IA: {e}")
        except Exception as e:
            print(f"Error saving stream to DB: {e}")

        del active_sessions[sid]
        socketio.emit('session_update', {'action': 'remove', 'id': sid})
    return {"status": "ok"}
