import os
import time
import json
import logging

logger = logging.getLogger(__name__)


def _do_process(audio_id, file_path, user_id, language='pt-BR'):
    """Lógica central de processamento — chamada pela task Celery ou thread fallback."""
    from app.services.audio_processor import denoiser, transcribe_audio
    from app.supabase_ext import supabase

    # Garante que o modelo está carregado
    if not denoiser.ensure_model_loaded():
        logger.warning(f"[audio {audio_id}] Modelo IA não disponível — abortando processamento.")
        supabase.table('audios').update({
            "processing_error": "Modelo IA não disponível"
        }).eq('id', audio_id).execute()
        return False

    start_time = time.time()
    try:
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()

        processed_bytes = denoiser.denoise_audio(audio_bytes)

        upload_dir = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        processed_filename = f"processed_{filename}"
        processed_path = os.path.join(upload_dir, processed_filename)

        with open(processed_path, 'wb') as f:
            f.write(processed_bytes)

        update_data = {
            "processed": True,
            "processed_path": processed_path,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "processing_error": None,
        }

        if transcribe_audio:
            try:
                transcription = transcribe_audio(processed_path, language=language)
                if transcription:
                    update_data["transcribed"] = True
                    update_data["transcription_text"] = transcription
            except Exception as te:
                logger.warning(f"[audio {audio_id}] Transcrição falhou: {te}")

        supabase.table('audios').update(update_data).eq('id', audio_id).execute()

        # Log do evento
        supabase.table('events').insert({
            "user_id": user_id, "event_type": "AUDIO_PROCESSED", "level": "info",
            "screen": "audio", "details_json": json.dumps({
                "audio_id": audio_id,
                "processing_time_ms": update_data["processing_time_ms"],
                "transcribed": update_data.get("transcribed", False),
            }),
        }).execute()

        # Notificação push
        try:
            from app.services.push_service import PushService
            PushService.send_push_notification(
                user_id=user_id, title="Áudio Processado",
                message=f"Seu áudio foi limpo pela IA e está pronto.",
                data_payload={"audio_id": audio_id},
            )
        except Exception:
            pass

        # Socket
        try:
            from app import socketio
            socketio.emit("audio_completed", {
                "audio_id": audio_id, "filename": filename,
                "message": "Processamento concluído!",
                "processing_time_ms": update_data["processing_time_ms"],
            }, namespace="/")
        except Exception:
            pass

        logger.info(f"[audio {audio_id}] Processado em {update_data['processing_time_ms']}ms")
        return True

    except Exception as e:
        import traceback
        logger.error(f"[audio {audio_id}] Erro no processamento: {e}\n{traceback.format_exc()}")
        try:
            from app.supabase_ext import supabase as sb
            sb.table('audios').update({
                "processing_error": str(e)[:300]
            }).eq('id', audio_id).execute()
        except Exception:
            pass
        return False



