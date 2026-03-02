from app.celery_ext import celery_app
import time

@celery_app.task
def process_audio_background(audio_id):
    """
    Exemplo de task em background para Celery (Item 4).
    Isso simula o processamento longo de redução de ruído/transcrição,
    liberando a API para o usuário imediatamente.
    """
    time.sleep(5) # Simula os 5 segundos gastando CPU localmente (PyTorch/Whisper)
    return f"Áudio {audio_id} processado com sucesso na fila em background"
