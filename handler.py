import runpod
import torch
import torchaudio
import base64
import io
import os
import soundfile as sf
from resemble_enhance.enhancer.inference import enhance, load_enhancer

# Modeli global alanda bir kere yüklüyoruz (Cold Start süresini kısaltmak için)
# CPU yerine GPU (cuda) kullandığından emin olalım.
device = "cuda" if torch.cuda.is_available() else "cpu"
run_dir = None # Varsayılan indirme konumu


print(f"Model yükleniyor... Device: {device}")
# İlk çalıştırmada modeli belleğe alıyoruz
enhancer = None

def get_enhancer():
    global enhancer
    if enhancer is None:
        # Modeli yükle (run_dir None ise varsayılan yerden çeker)
        enhancer = load_enhancer(run_dir, device)
    return enhancer

def handler(job):
    job_input = job["input"]
    
    # Girdiden ses verisini al (Base64 formatında bekleniyor)
    audio_base64 = job_input.get("audio_base64")
    
    if not audio_base64:
        return {"error": "Lutfen 'audio_base64' parametresini gonderin."}

    try:
        # Base64'ü ses dosyasına çevir
        audio_bytes = base64.b64decode(audio_base64)
        audio_buffer = io.BytesIO(audio_bytes)
        
        # Sesi yükle (Torchaudio veya Soundfile ile)
        info = torchaudio.info(audio_buffer) # Format kontrolü
        waveform, sr = torchaudio.load(audio_buffer)
        
        # Modeli getir
        model = get_enhancer()
        
        # İŞLEME (Enhance)
        # nfe=64 varsayılan değerdir, kalite/hız dengesi için düşürülebilir.
        enhanced_wav, new_sr = enhance(
            waveform, 
            sr, 
            device, 
            nfe=64, 
            solver="midpoint", 
            lambd=0.5, 
            tau=0.5
        )

        # Sonucu tekrar bellekteki bir dosyaya yaz
        output_buffer = io.BytesIO()
        torchaudio.save(output_buffer, enhanced_wav.cpu(), new_sr, format="wav")
        output_buffer.seek(0)
        
        # Sonucu Base64'e çevir
        output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        return {
            "enhanced_audio": output_base64,
            "sample_rate": new_sr
        }

    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
