FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /

# Build sırasında etkileşimi kapatmak için
ARG DEBIAN_FRONTEND=noninteractive

# Huggingface token zorunlu (pocket-tts'in voice-clone'lu modeli için)
ARG HF_TOKEN

# HF_TOKEN kontrolü
RUN if [ -z "$HF_TOKEN" ]; then \
        echo ""; \
        echo "Hata: Voice cloning için HuggingFace token gereklidir."; \
        echo ""; \
        exit 1; \
    fi

# 1. Sistem Bağımlılıklarını Kur
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    psmisc \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# 2. Ana Python Ortamı İçin Temel Paketleri Kur
RUN pip install --upgrade pip && \
    pip install --no-cache-dir runpod requests

# 3. Resemble-Enhance Sanal Ortamını Hazırla
RUN python -m venv /root/venv_resemble && \
    /root/venv_resemble/bin/pip install --upgrade pip && \
    /root/venv_resemble/bin/pip install fastapi uvicorn resemble-enhance

# 4. Pocket-TTS Sanal Ortamını Hazırla
RUN python -m venv /root/venv_pocket && \
    /root/venv_pocket/bin/pip install --upgrade pip && \
    /root/venv_pocket/bin/pip install fastapi uvicorn git+https://github.com/kyutai-labs/pocket-tts

# 5. Dosyaları İmajın İçine Kopyala
COPY handler.py api_enhance.py api_pocket.py /

# 6. MODELLERİ ÖNCEDEN İNDİR (Cold Start Optimizasyonu)
# Bu adım, imajı oluştururken modelleri indirir, böylece çalışma anında internete ihtiyaç duymaz.
RUN HF_TOKEN=$HF_TOKEN /root/venv_resemble/bin/python -c "from resemble_enhance.enhancer.inference import load_enhancer; load_enhancer(None, 'cpu')" && \
    echo "✅ Resemble-Enhance modeli indirildi" && \
    HF_TOKEN=$HF_TOKEN /root/venv_pocket/bin/python -c "from pocket_tts import TTSModel; TTSModel.load_model()" && \
    echo "✅ Pocket-TTS voice cloning modeli indirildi"

# Model indirildikten sonra offline modu aktif et
ENV HF_HUB_OFFLINE=1

# 7. Başlatma Komutu
# -u flag'i logların anlık olarak RunPod panelinde görünmesini sağlar
CMD ["python", "-u", "/handler.py"]
