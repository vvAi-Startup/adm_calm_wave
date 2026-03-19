import os
import io
import soundfile as sf
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AudioDenoiser:
    """
    Stub de denoising — funcionalidade desativada neste ambiente de deploy.
    torch/torchaudio foram removidos para viabilizar o build no Render (free tier).
    Para reativar, reinstale as dependências e restaure a implementação completa.
    """

    def ensure_model_loaded(self) -> bool:
        return False

    def denoise_audio(self, audio_bytes: bytes) -> bytes:
        raise NotImplementedError(
            "Denoising desativado: torch não está instalado neste ambiente."
        )


def transcribe_audio(audio_path: str, language: str = "pt-BR") -> str:
    """Transcreve o áudio para texto usando SpeechRecognition."""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment

        wav_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            wav_path = audio_path + ".wav"
            audio = AudioSegment.from_file(audio_path)
            audio.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            if language and language != "auto":
                text = recognizer.recognize_google(audio_data, language=language)
            else:
                text = recognizer.recognize_google(audio_data)

        if wav_path != audio_path and os.path.exists(wav_path):
            os.remove(wav_path)

        return text
    except ImportError:
        logger.error("Bibliotecas SpeechRecognition ou pydub não instaladas.")
        return ""
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        return ""


# Instância global — denoising desativado neste ambiente
denoiser = AudioDenoiser()


def get_audio_duration(file_path: str) -> float:
    """Retorna duração do áudio em segundos. Retorna 0 em caso de erro."""
    try:
        info = sf.info(file_path)
        return round(info.duration, 2)
    except Exception:
        try:
            audio_np, sr_rate = sf.read(file_path)
            return round(len(audio_np) / sr_rate, 2)
        except Exception:
            return 0.0
