import runpod
import torch
import torchaudio
import base64
import io
import soundfile as sf  # Soundfile kütüphanesini kullanacağız
from resemble_enhance.enhancer.inference import enhance, load_enhancer

# Cihaz seçimi
device = "cuda" if torch.cuda.is_available() else "cpu"
run_dir = None 

print(f"Model yükleniyor... Device: {device}")
enhancer = None

def get_enhancer():
    global enhancer
    if enhancer is None:
        enhancer = load_enhancer(run_dir, device)
    return enhancer

def handler(job):
    job_input = job["input"]
    audio_base64 = job_input.get("audio_base64")
    
    if not audio_base64:
        return {"error": "Lutfen 'audio_base64' parametresini gonderin."}

    try:
        # 1. Base64 çözme
        audio_bytes = base64.b64decode(audio_base64)
        audio_buffer = io.BytesIO(audio_bytes)
        
        # 2. SES OKUMA (DÜZELTME BURADA)
        data, sr = sf.read(audio_buffer)
        waveform = torch.from_numpy(data).float()
        
        # Soundfile kütüphanesi çıktıları şöyledir:
        # Mono ses: (Zaman,) -> 1 Boyutlu
        # Stereo ses: (Zaman, KanalSayısı) -> 2 Boyutlu
        
        # HATA ÇÖZÜMÜ:
        # Resemble Enhance SADECE 1D (Mono) istiyor.
        # Eğer veri 2D ise (yani Stereo ise veya yanlış boyutluysa), Mono'ya çeviriyoruz.
        if waveform.dim() > 1:
            # Kanalların ortalamasını alarak Mono yapıyoruz
            # (Time, Channels) olduğu için dim=1'i sıkıştırıyoruz.
            waveform = waveform.mean(dim=1)
            
        # ŞU AN: waveform değişkeni kesinlikle 1D (sadece [Zaman]) formatında.
            
        # 3. Enhance işlemi
        model = get_enhancer()
        
        enhanced_wav, new_sr = enhance(
            waveform, 
            sr, 
            device, 
            nfe=64, 
            solver="midpoint", 
            lambd=0.5, 
            tau=0.5
        )

        # 4. Sonucu kaydetme
        output_buffer = io.BytesIO()
        # Kaydederken (Kanal, Zaman) formatı genelde daha iyidir, o yüzden unsqueeze yapıyoruz
        # ama torchaudio 1D de kabul eder. Garanti olsun diye 1D gönderiyoruz.
        torchaudio.save(output_buffer, enhanced_wav.cpu().unsqueeze(0), new_sr, format="wav")
        output_buffer.seek(0)
        
        output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        return {
            "enhanced_audio": output_base64,
            "sample_rate": new_sr
        }

    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

runpod.serverless.start({"handler": handler})
