from fastapi import FastAPI
from pydantic import BaseModel
import torch, torchaudio
from resemble_enhance.enhancer.inference import enhance, load_enhancer
import uvicorn
import os

# os.environ["HF_TOKEN"] = "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Hugging Face token

app = FastAPI()
device = "cuda" if torch.cuda.is_available() else "cpu"
enhancer = load_enhancer(None, device)

class EnhanceRequest(BaseModel):
    input_path: str
    output_path: str
    nfe: int = 64
    solver: str = "midpoint"
    lambd: float = 0.5
    tau: float = 0.5

@app.post("/process")
async def process(req: EnhanceRequest):
    waveform, sr = torchaudio.load(req.input_path)
    if waveform.shape[0] > 1: waveform = waveform.mean(dim=0, keepdim=True)
    
    # Dinamik parametrelerle çalıştırma
    enhanced_wav, new_sr = enhance(
        waveform.squeeze(), sr, device, 
        nfe=req.nfe, solver=req.solver, lambd=req.lambd, tau=req.tau
    )
    
    torchaudio.save(req.output_path, enhanced_wav.cpu().unsqueeze(0), new_sr)
    return {"status": "ok", "new_sr": new_sr}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8011)