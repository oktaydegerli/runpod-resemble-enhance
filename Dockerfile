# Temel imaj olarak CUDA destekli bir PyTorch imajı kullanıyoruz
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

WORKDIR /

ARG DEBIAN_FRONTEND=noninteractive
ARG HF_TOKEN

# HF_TOKEN kontrolü
RUN if [ -z "$HF_TOKEN" ]; then \
        echo "❌ HATA: HF_TOKEN build argument'i eksik!"; \
        exit 1; \
    fi

# 1. Sistem Bağımlılıklarını Kur ve HEMEN temizle
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    psmisc \
    && git lfs install \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

# 2. Ana Python Ortamı - cache temizle
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir runpod requests

# 3. Resemble-Enhance Sanal Ortamı
RUN python -m venv /root/venv_resemble && \
    /root/venv_resemble/bin/pip install --upgrade pip && \
    /root/venv_resemble/bin/pip install --no-cache-dir fastapi uvicorn resemble-enhance

# 4. Pocket-TTS Sanal Ortamı
RUN python -m venv /root/venv_pocket && \
    /root/venv_pocket/bin/pip install --upgrade pip && \
    /root/venv_pocket/bin/pip install --no-cache-dir fastapi uvicorn git+https://github.com/kyutai-labs/pocket-tts

# 5. Dosyaları kopyala
COPY handler.py api_enhance.py api_pocket.py /

# 6. Modelleri indir VE pip cache'i temizle
RUN HF_TOKEN=$HF_TOKEN /root/venv_resemble/bin/python -c "from resemble_enhance.enhancer.inference import load_enhancer; load_enhancer(None, 'cpu')" && \
    echo "✅ Resemble-Enhance modeli indirildi" && \
    HF_TOKEN=$HF_TOKEN /root/venv_pocket/bin/python -c "from pocket_tts import TTSModel; TTSModel.load_model()" && \
    echo "✅ Pocket-TTS voice cloning modeli indirildi" && \
    /root/venv_pocket/bin/pip cache purge && \
    /root/venv_resemble/bin/pip cache purge && \
    python -m pip cache purge && \
    rm -rf /tmp/* && \
    rm -rf /root/.cache/pip

ENV HF_HUB_OFFLINE=1

CMD ["python", "-u", "/handler.py"]
