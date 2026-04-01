import os
import io
import soundfile as sf
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ─── IMPORTS PESADOS SÃO LAZY ─────────────────────────────────────────────────
# torch, numpy e torchaudio NÃO são importados aqui para não atrasar o startup.
# São carregados apenas na primeira chamada a ensure_model_loaded().
# ──────────────────────────────────────────────────────────────────────────────

class Settings:
    SAMPLE_RATE = 44100
    SEGMENT_LENGTH = 44100 * 2  # 2 seconds
    N_FFT = 1024
    HOP_LENGTH = 256
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "best_denoiser_model.pth")

settings = Settings()


class AudioDenoiser:
    """Classe responsável pelo processamento de áudio com denoising"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model = None
        self.device = None
        self._torch = None
        self._nn = None
        self._F = None
        self._torchaudio = None
        self._np = None

    def _lazy_imports(self):
        """Importa torch e numpy somente quando necessário (primeira chamada)."""
        if self._torch is not None:
            return
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        import torchaudio
        import numpy as np
        self._torch = torch
        self._nn = nn
        self._F = F
        self._torchaudio = torchaudio
        self._np = np
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _build_unet(self):
        """Constrói a classe UNetDenoiser usando nn já importado."""
        torch = self._torch
        nn = self._nn
        F = self._F

        class UNetDenoiser(nn.Module):
            def __init__(self_inner):
                super().__init__()
                self_inner.enc1 = self_inner._encoder_block(1, 16)
                self_inner.enc2 = self_inner._encoder_block(16, 32)
                self_inner.enc3 = self_inner._encoder_block(32, 64)
                self_inner.enc4 = self_inner._encoder_block(64, 128)
                self_inner.bottleneck = nn.Sequential(
                    nn.Conv2d(128, 256, kernel_size=3, padding=1),
                    nn.BatchNorm2d(256), nn.LeakyReLU(0.2),
                    nn.Conv2d(256, 256, kernel_size=3, padding=1),
                    nn.BatchNorm2d(256), nn.LeakyReLU(0.2),
                    nn.Dropout(0.5)
                )
                self_inner.dec4 = self_inner._decoder_block(256 + 128, 128)
                self_inner.dec3 = self_inner._decoder_block(128 + 64, 64)
                self_inner.dec2 = self_inner._decoder_block(64 + 32, 32)
                self_inner.dec1 = self_inner._decoder_block(32 + 16, 16)
                self_inner.final = nn.Sequential(
                    nn.Conv2d(16, 1, kernel_size=1),
                    nn.Sigmoid()
                )

            def _encoder_block(self_inner, in_channels, out_channels):
                return nn.Sequential(
                    nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
                    nn.BatchNorm2d(out_channels), nn.LeakyReLU(0.2),
                    nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                    nn.BatchNorm2d(out_channels), nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2)
                )

            def _decoder_block(self_inner, in_channels, out_channels):
                return nn.Sequential(
                    nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
                    nn.BatchNorm2d(out_channels), nn.LeakyReLU(0.2),
                    nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                    nn.BatchNorm2d(out_channels), nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(out_channels, out_channels, kernel_size=2, stride=2)
                )

            def _crop_tensor(self_inner, source, target):
                _, _, h_source, w_source = source.size()
                _, _, h_target, w_target = target.size()
                h_diff = (h_source - h_target) // 2
                w_diff = (w_source - w_target) // 2
                if h_diff < 0 or w_diff < 0:
                    return F.interpolate(source, size=(h_target, w_target), mode='bilinear', align_corners=False)
                return source[:, :, h_diff:h_diff+h_target, w_diff:w_diff+w_target]

            def forward(self_inner, x):
                enc1_out = self_inner.enc1(x)
                enc2_out = self_inner.enc2(enc1_out)
                enc3_out = self_inner.enc3(enc2_out)
                enc4_out = self_inner.enc4(enc3_out)
                bottleneck_out = self_inner.bottleneck(enc4_out)
                dec4_out = self_inner.dec4(torch.cat([bottleneck_out, self_inner._crop_tensor(enc4_out, bottleneck_out)], dim=1))
                dec3_out = self_inner.dec3(torch.cat([dec4_out, self_inner._crop_tensor(enc3_out, dec4_out)], dim=1))
                dec2_out = self_inner.dec2(torch.cat([dec3_out, self_inner._crop_tensor(enc2_out, dec3_out)], dim=1))
                dec1_out = self_inner.dec1(torch.cat([dec2_out, self_inner._crop_tensor(enc1_out, dec2_out)], dim=1))
                mask = self_inner.final(dec1_out)
                if mask.size() != x.size():
                    mask = F.interpolate(mask, size=(x.size(2), x.size(3)), mode='bilinear', align_corners=False)
                return mask

        return UNetDenoiser

    def load_model(self) -> None:
        """Carrega o modelo U-Net pré-treinado"""
        self._lazy_imports()
        torch = self._torch

        if not os.path.exists(self.model_path):
            logger.warning(f"Arquivo do modelo '{self.model_path}' não encontrado. O processamento não funcionará.")
            return
        
        try:
            UNetDenoiser = self._build_unet()
            self.model = UNetDenoiser().to(self.device)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
            logger.info("Modelo de denoising carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            self.model = None
        
    def preprocess_audio(self, audio_bytes: bytes):
        """Pré-processa o áudio carregado"""
        torch = self._torch
        torchaudio = self._torchaudio
        buffer = io.BytesIO(audio_bytes)
        audio_np, sr = sf.read(buffer)
        
        if len(audio_np.shape) == 1:
            noisy_audio = torch.from_numpy(audio_np).float().unsqueeze(0)
        else:
            noisy_audio = torch.from_numpy(audio_np).float().t()
            
        if sr != settings.SAMPLE_RATE:
            noisy_audio = torchaudio.transforms.Resample(sr, settings.SAMPLE_RATE)(noisy_audio)
        
        if noisy_audio.shape[0] > 1:
            noisy_audio = torch.mean(noisy_audio, dim=0, keepdim=True)
        
        noisy_audio = noisy_audio / (torch.max(torch.abs(noisy_audio)) + 1e-8)
        return noisy_audio, noisy_audio.shape[1]
    
    def process_audio_segment(self, chunk):
        """Processa um segmento de áudio"""
        torch = self._torch
        F = self._F
        current_length = chunk.shape[1]
        if current_length < settings.SEGMENT_LENGTH:
            chunk = F.pad(chunk, (0, settings.SEGMENT_LENGTH - current_length))

        stft = torch.stft(
            chunk.squeeze(0), 
            n_fft=settings.N_FFT, 
            hop_length=settings.HOP_LENGTH, 
            window=torch.hann_window(settings.N_FFT), 
            return_complex=True
        )
        mag = torch.log1p(torch.abs(stft))
        phase = torch.angle(stft)
        noisy_spec = {'magnitude': mag.to(self.device), 'phase': phase.to(self.device)}
        mask = self.model(noisy_spec['magnitude'].unsqueeze(0).unsqueeze(0))
        return self._reconstruct_audio(noisy_spec, mask, settings.HOP_LENGTH, settings.SEGMENT_LENGTH)
    
    def _reconstruct_audio(self, noisy_spec, mask, hop_length, length):
        """Reconstrói o áudio a partir do espectrograma e máscara"""
        torch = self._torch
        magnitude = torch.exp(noisy_spec['magnitude']) - 1
        enhanced_magnitude = magnitude * mask.squeeze()
        enhanced_stft = enhanced_magnitude * torch.exp(1j * noisy_spec['phase'])
        audio = torch.istft(
            enhanced_stft, n_fft=settings.N_FFT, hop_length=hop_length,
            window=torch.hann_window(settings.N_FFT, device=enhanced_stft.device), length=length
        )
        return audio
    
    def ensure_model_loaded(self) -> bool:
        """Carrega o modelo se ainda não estiver carregado. Retorna True se ok."""
        if self.model is None:
            self.load_model()
        return self.model is not None

    def denoise_audio(self, audio_bytes: bytes) -> bytes:
        """Remove ruído do áudio e retorna os bytes do áudio processado"""
        torch = self._torch
        np = self._np
        if self.model is None:
            raise RuntimeError("Modelo não está carregado")
        
        noisy_audio, original_length = self.preprocess_audio(audio_bytes)
        denoised_chunks = []
        num_segments = int(np.ceil(original_length / settings.SEGMENT_LENGTH))

        with torch.no_grad():
            for i in range(num_segments):
                start = i * settings.SEGMENT_LENGTH
                end = start + settings.SEGMENT_LENGTH
                chunk = noisy_audio[:, start:end]
                denoised_chunk = self.process_audio_segment(chunk)
                denoised_chunks.append(denoised_chunk.cpu())

        full_denoised_audio = torch.cat(denoised_chunks, dim=0)[:original_length]
        denoised_np = full_denoised_audio.detach().numpy()
        denoised_np = denoised_np / np.max(np.abs(denoised_np))

        output_buffer = io.BytesIO()
        sf.write(output_buffer, denoised_np, settings.SAMPLE_RATE, format='WAV')
        output_buffer.seek(0)
        return output_buffer.getvalue()

def transcribe_audio(audio_path: str, language: str = "pt-BR") -> str:
    """Transcreve o áudio para texto usando SpeechRecognition e modelo respectivo de idioma"""
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
        
        # Converter para WAV se não for (SpeechRecognition funciona melhor com WAV)
        wav_path = audio_path
        if not audio_path.lower().endswith('.wav'):
            wav_path = audio_path + ".wav"
            audio = AudioSegment.from_file(audio_path)
            audio.export(wav_path, format="wav")
            
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            # Ajusta para o ruído ambiente
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            # Tenta reconhecer usando o idioma desejado
            if language and language != "auto":
                text = recognizer.recognize_google(audio_data, language=language)
            else:
                text = recognizer.recognize_google(audio_data)
            
        # Limpa arquivo temporário se foi criado
        if wav_path != audio_path and os.path.exists(wav_path):
            os.remove(wav_path)
            
        return text
    except ImportError:
        logger.error("Bibliotecas SpeechRecognition ou pydub não instaladas.")
        return ""
    except sr.UnknownValueError:
        logger.warning("Google Speech Recognition não conseguiu entender o áudio")
        return ""
    except sr.RequestError as e:
        logger.error(f"Erro ao requisitar resultados do serviço Google Speech Recognition; {e}")
        return ""
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        return ""

# Instância global — modelo carregado sob demanda (lazy)
denoiser = AudioDenoiser()


def get_audio_duration(file_path: str) -> float:
    """Retorna duração do áudio em segundos. Retorna 0 em caso de erro."""
    try:
        info = sf.info(file_path)
        return round(info.duration, 2)
    except Exception:
        try:
            audio_np, sr = sf.read(file_path)
            return round(len(audio_np) / sr, 2)
        except Exception:
            return 0.0
