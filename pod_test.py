import base64
import os
import time
# handler.py dosyasından gerekli fonksiyonları içe aktar
from handler import handler, start_backend_services

def run_test():
    # --- 1. ORTAMI SIFIRLA VE BAŞLAT ---
    print("🔄 Test ortamı hazırlanıyor (Portlar temizleniyor ve modeller yükleniyor)...")
    start_backend_services()
    
    # --- 2. AYARLAR ---
    INPUT_FILE = "test.wav" # Pod'da bu dosya bulunmalı
    OUTPUT_WAV = "result_enhanced.wav"
    OUTPUT_SAFETENSORS = "result_prompt.safetensors"

    if not os.path.exists(INPUT_FILE):
        print(f"❌ HATA: {INPUT_FILE} bulunamadı! Lütfen bir test dosyası yükleyin.")
        return

    # --- 3. INPUT HAZIRLA ---
    with open(INPUT_FILE, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')

    job = {
        "input": {
            "audio_base64": b64_data,
            "nfe": 32, # Hızlı test için
            "return_enhanced_audio": True
        }
    }

    # --- 4. ÇALIŞTIR ---
    print("🚀 Test işlemi başlatıldı...")
    start_t = time.time()
    response = handler(job)
    end_t = time.time()

    # --- 5. SONUÇLARI DEĞERLENDİR ---
    if "error" in response:
        print(f"❌ TEST BAŞARISIZ: {response['error']}")
    else:
        print(f"✅ TEST BAŞARILI! Toplam İşlem Süresi: {end_t - start_t:.2f}s")
        
        # Prompt dosyasını kaydet
        with open(OUTPUT_SAFETENSORS, "wb") as f:
            f.write(base64.b64decode(response["prompt_base64"]))
        print(f"💾 Prompt kaydedildi: {OUTPUT_SAFETENSORS}")

        # İyileştirilmiş sesi kaydet
        if "enhanced_audio_base64" in response:
            with open(OUTPUT_WAV, "wb") as f:
                f.write(base64.b64decode(response["enhanced_audio_base64"]))
            print(f"💾 İyileştirilmiş ses kaydedildi: {OUTPUT_WAV}")

if __name__ == "__main__":
    run_test()