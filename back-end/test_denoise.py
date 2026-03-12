import os
from app.services.audio_processor import denoiser
import soundfile as sf
import numpy as np
from datetime import datetime
import json
import time

try:
    print("Testando carregamento do modelo...")
    loaded = denoiser.ensure_model_loaded()
    print("Modelo carregado:", loaded)

    print("Gerando audio fake para teste (ruido)...")
    sample_rate = 44100
    duration = 3  # 3 segundos
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    noise = np.random.normal(0, 0.5, t.shape)
    
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    fake_path = os.path.join(upload_dir, "fake_test_noise.wav")
    
    sf.write(fake_path, noise, sample_rate)
    
    print("Efetuando denoise do audio...")
    start_t = time.time()
    with open(fake_path, 'rb') as f:
        raw = f.read()
    
    processed_bytes = denoiser.denoise_audio(raw)
    
    print(f"Denoise finalizado com sucesso em {time.time() - start_t:.2f} segundos!")
    print(f"Bytes retornados: {len(processed_bytes)}")

except Exception as e:
    import traceback
    print("ERRO DURANTE O TESTE:")
    traceback.print_exc()
