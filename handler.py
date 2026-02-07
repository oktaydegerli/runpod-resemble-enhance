import runpod
import subprocess
import requests
import time
import base64
import os
import uuid
import signal

# --- AYARLAR VE YOLLAR ---
RESEMBLE_PYTHON = "/root/venv_resemble/bin/python"
POCKET_PYTHON = "/root/venv_pocket/bin/python"
RESEMBLE_PORT = 8011
POCKET_PORT = 8012

def kill_process_on_port(port):
    """Portu işgal eden süreci temizler."""
    try:
        # fuser komutu portu kullanan süreci kapatır (psmisc paketi gereklidir)
        subprocess.run(["fuser", "-k", f"{port}/tcp"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception:
        pass

def wait_for_services():
    """Modeller belleğe yüklenip API'ler hazır olana kadar bekler."""
    start_time = time.time()
    services = {
        "Resemble Enhance": f"http://127.0.0.1:{RESEMBLE_PORT}/docs",
        "Pocket-TTS": f"http://127.0.0.1:{POCKET_PORT}/docs"
    }
    
    for name, url in services.items():
        ready = False
        while not ready:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    ready = True
                    print(f"✅ {name} hazır! ({time.time() - start_time:.2f}s)")
            except requests.exceptions.ConnectionError:
                if time.time() - start_time > 120:
                    raise Exception(f"❌ {name} yükleme zaman aşımı!")
                time.sleep(0.5)

def start_backend_services():
    """Eski süreçleri öldürür ve yeni API servislerini başlatır."""
    print("🧹 Portlar temizleniyor...")
    kill_process_on_port(RESEMBLE_PORT)
    kill_process_on_port(POCKET_PORT)
    time.sleep(1)

    print(f"🛠️ Servisler başlatılıyor (Portlar: {RESEMBLE_PORT}, {POCKET_PORT})...")
    # api_enhance.py ve api_pocket.py dosyalarının aynı dizinde olduğu varsayılır
    subprocess.Popen([RESEMBLE_PYTHON, "api_enhance.py"])
    subprocess.Popen([POCKET_PYTHON, "api_pocket.py"])
    
    wait_for_services()

def handler(job):
    """RunPod ana işlem fonksiyonu"""
    job_input = job['input']
    
    # Parametreleri al
    audio_base64 = job_input.get("audio_base64")
    nfe = job_input.get("nfe", 64)
    solver = job_input.get("solver", "midpoint")
    lambd = job_input.get("lambd", 0.5)
    tau = job_input.get("tau", 0.5)
    return_enhanced = job_input.get("return_enhanced_audio", False)

    if not audio_base64:
        return {"error": "audio_base64 zorunludur."}

    # UUID ile çakışmaları önle
    req_id = str(uuid.uuid4())
    in_wav = f"/tmp/in_{req_id}.wav"
    enh_wav = f"/tmp/enh_{req_id}.wav"
    out_safetensors = f"/tmp/out_{req_id}.safetensors"

    try:
        # 1. Base64'ten Dosyaya
        with open(in_wav, "wb") as f:
            f.write(base64.b64decode(audio_base64))

        # 2. Resemble Enhance API Çağrısı
        res1 = requests.post(f"http://127.0.0.1:{RESEMBLE_PORT}/process", json={
            "input_path": in_wav, "output_path": enh_wav,
            "nfe": nfe, "solver": solver, "lambd": lambd, "tau": tau
        })
        if res1.status_code != 200: return {"error": f"Enhance Hatası: {res1.text}"}

        # 3. Pocket-TTS API Çağrısı
        res2 = requests.post(f"http://127.0.0.1:{POCKET_PORT}/process", json={
            "input_path": enh_wav, "output_path": out_safetensors
        })
        if res2.status_code != 200: return {"error": f"Pocket Hatası: {res2.text}"}

        # 4. Sonuçları Hazırla
        response = {"status": "success"}
        with open(out_safetensors, "rb") as f:
            response["prompt_base64"] = base64.b64encode(f.read()).decode('utf-8')
        
        if return_enhanced:
            with open(enh_wav, "rb") as f:
                response["enhanced_audio_base64"] = base64.b64encode(f.read()).decode('utf-8')

        return response

    except Exception as e:
        return {"error": str(e)}
    finally:
        # Geçici dosyaları temizle
        for f in [in_wav, enh_wav, out_safetensors]:
            if os.path.exists(f): os.remove(f)

# RunPod Serverless Modu
if __name__ == "__main__":
    start_backend_services()
    runpod.serverless.start({"handler": handler})