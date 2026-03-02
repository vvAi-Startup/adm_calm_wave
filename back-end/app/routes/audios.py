from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.audio import Audio
import os
import time
from werkzeug.utils import secure_filename

audios_bp = Blueprint("audios", __name__)

# Import the denoiser
try:
    from app.services.audio_processor import denoiser, transcribe_audio
except ImportError:
    denoiser = None
    transcribe_audio = None
    print("Warning: Audio processor not available")

@audios_bp.route("/play/<int:audio_id>", methods=["GET"])
def play_audio(audio_id):
    audio = Audio.query.get_or_404(audio_id)
    
    audio_type = request.args.get("type", "processed")
    
    if audio_type == "original":
        file_path = audio.file_path
    else:
        # Prefer processed path if available, fallback to original
        file_path = audio.processed_path if audio.processed and audio.processed_path else audio.file_path
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Arquivo de áudio não encontrado"}), 404
        
    # Use conditional response to support range requests (important for audio streaming/seeking in browsers)
    response = send_file(file_path, mimetype="audio/wav", conditional=True)
    # Add headers to prevent caching issues with audio files
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
        
    user_id = get_jwt_identity()
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    # Create DB entry
    audio = Audio(
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        size_bytes=os.path.getsize(file_path),
        device_origin=request.form.get("device_origin", "Web")
    )
    db.session.add(audio)
    
    # Log upload event
    from app.models.other import Event
    import json
    upload_event = Event(
        user_id=user_id,
        event_type="AUDIO_UPLOADED",
        level="info",
        screen="audio",
        details_json=json.dumps({"filename": filename, "size": audio.size_bytes})
    )
    db.session.add(upload_event)
    db.session.commit()
    
    # Process audio if denoiser is available
    if denoiser and denoiser.model is not None:
        try:
            start_time = time.time()
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
                
            processed_bytes = denoiser.denoise_audio(audio_bytes)
            
            processed_filename = f"processed_{filename}"
            processed_path = os.path.join(upload_dir, processed_filename)
            
            with open(processed_path, 'wb') as f:
                f.write(processed_bytes)
                
            audio.processed = True
            audio.processed_path = processed_path
            audio.processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Transcribe audio
            if transcribe_audio:
                print("Transcribing audio...")
                transcription = transcribe_audio(processed_path)
                if transcription:
                    audio.transcribed = True
                    audio.transcription_text = transcription
                    print(f"Transcription successful: {transcription[:50]}...")
            
            # Log success event
            success_event = Event(
                user_id=user_id,
                event_type="AUDIO_PROCESSED",
                level="info",
                screen="audio",
                details_json=json.dumps({
                    "audio_id": audio.id, 
                    "processing_time_ms": audio.processing_time_ms,
                    "transcribed": audio.transcribed
                })
            )
            db.session.add(success_event)
            db.session.commit()
            print(f"Audio processed successfully in {audio.processing_time_ms}ms")
            
        except Exception as e:
            import traceback
            print(f"Error processing audio: {e}")
            traceback.print_exc()
            
            # Log error event
            error_event = Event(
                user_id=user_id,
                event_type="AUDIO_PROCESSING_FAILED",
                level="error",
                screen="audio",
                details_json=json.dumps({"error": str(e)})
            )
            db.session.add(error_event)
            db.session.commit()
            
    return jsonify({"audio": audio.to_dict()}), 201

@audios_bp.route("/", methods=["GET"])
@jwt_required()
def list_audios():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    processed = request.args.get("processed", None)
    favorite = request.args.get("favorite", None)

    query = Audio.query
    if processed is not None:
        query = query.filter(Audio.processed == (processed == "true"))
    if favorite is not None:
        query = query.filter(Audio.favorite == (favorite == "true"))

    pagination = query.order_by(Audio.recorded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify(
        {
            "audios": [a.to_dict() for a in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
        }
    )


@audios_bp.route("/", methods=["POST"])
@jwt_required()
def create_audio():
    data = request.get_json()
    audio = Audio(
        user_id=data["user_id"],
        filename=data["filename"],
        file_path=data.get("file_path"),
        duration_seconds=data.get("duration_seconds", 0),
        size_bytes=data.get("size_bytes", 0),
        device_origin=data.get("device_origin"),
    )
    db.session.add(audio)
    db.session.commit()
    return jsonify({"audio": audio.to_dict()}), 201


@audios_bp.route("/<int:audio_id>", methods=["GET"])
@jwt_required()
def get_audio(audio_id):
    audio = Audio.query.get_or_404(audio_id)
    return jsonify({"audio": audio.to_dict()})


@audios_bp.route("/<int:audio_id>", methods=["PUT"])
@jwt_required()
def update_audio(audio_id):
    current_user_id = get_jwt_identity()
    audio = Audio.query.get_or_404(audio_id)
    data = request.get_json()
    
    changes = {}
    for field in ["processed", "transcribed", "favorite", "transcription_text", "playlist_id"]:
        if field in data:
            old_val = getattr(audio, field)
            new_val = data[field]
            if old_val != new_val:
                changes[field] = {"old": old_val, "new": new_val}
            setattr(audio, field, new_val)
            
    if changes:
        from app.models.other import Event
        import json
        update_event = Event(
            user_id=current_user_id,
            event_type="AUDIO_UPDATED",
            level="info",
            screen="audios",
            details_json=json.dumps({"audio_id": audio_id, "changes": changes})
        )
        db.session.add(update_event)
        
    db.session.commit()
    return jsonify({"audio": audio.to_dict()})


@audios_bp.route("/<int:audio_id>", methods=["DELETE"])
@jwt_required()
def delete_audio(audio_id):
    current_user_id = get_jwt_identity()
    audio = Audio.query.get_or_404(audio_id)
    
    from app.models.other import Event
    import json
    delete_event = Event(
        user_id=current_user_id,
        event_type="AUDIO_DELETED",
        level="warn",
        screen="audios",
        details_json=json.dumps({"audio_id": audio_id, "filename": audio.filename})
    )
    db.session.add(delete_event)
    
    db.session.delete(audio)
    db.session.commit()
    return jsonify({"message": "Áudio removido com sucesso"})
