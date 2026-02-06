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
        # Torchaudio yerine Soundfile kullanıyoruz.
        # Soundfile veriyi (Zaman, Kanal) formatında numpy array olarak döndürür.
        data, sr = sf.read(audio_buffer)
        
        # Numpy array'i PyTorch Tensor'a çeviriyoruz
        waveform = torch.from_numpy(data).float()
        
        # Resemble Enhance (Kanal, Zaman) formatı bekler.
        # Eğer ses Mono ise (Zaman,) -> (1, Zaman) yapmalıyız.
        # Eğer ses Stereo ise (Zaman, Kanal) -> (Kanal, Zaman) yapmalıyız.
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0) # Mono düzeltme
        else:
            waveform = waveform.t() # Stereo düzeltme (Transpose)
            
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
        # Çıktı için torchaudio.save kullanabiliriz, o sorunsuzdur.
        output_buffer = io.BytesIO()
        torchaudio.save(output_buffer, enhanced_wav.cpu(), new_sr, format="wav")
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
