from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pocket_tts import TTSModel
import uvicorn
import os

# os.environ["HF_TOKEN"] = "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Hugging Face token

app = FastAPI()

# Modeli globalde yükle (Bellekte sıcak tutar)
print("🚀 [Pocket-TTS] Model belleğe yükleniyor...")
try:
    model = TTSModel.load_model()
    print("✅ [Pocket-TTS] Model başarıyla yüklendi.")
except Exception as e:
    print(f"❌ [Pocket-TTS] Model yükleme hatası: {e}")

# Handler'dan gelen veriyi karşılayan model
class PocketRequest(BaseModel):
    input_path: str
    output_path: str

@app.post("/process")
async def process(req: PocketRequest):
    # Giriş dosyası var mı kontrol et
    if not os.path.exists(req.input_path):
        raise HTTPException(status_code=400, detail=f"Giriş dosyası bulunamadı: {req.input_path}")
    
    try:
        # Pocket-TTS Prompt oluşturma işlemi
        # Bu fonksiyon genelde bir tensor (.safetensors dosyası) üretir
        model.save_audio_prompt(req.input_path, req.output_path)
        
        return {"status": "ok", "message": "Prompt başarıyla oluşturuldu."}
    
    except Exception as e:
        print(f"❌ [Pocket-Process] Hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8012)