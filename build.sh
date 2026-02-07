apt-get update
apt-get install -y git git-lfs ffmpeg libsndfile1 psmisc
pip install --upgrade pip
pip install --no-cache-dir runpod
git lfs install
rm -rf /var/lib/apt/lists/*

python -m venv venv_resemble
source venv_resemble/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn
pip install resemble-enhance
from resemble_enhance.enhancer.inference import load_enhancer; load_enhancer(None, 'cpu')
deactivate

python -m venv venv_pocket
source venv_pocket/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn
pip install git+https://github.com/kyutai-labs/pocket-tts
from pocket_tts import TTSModel; TTSModel.load_model()
deactivate