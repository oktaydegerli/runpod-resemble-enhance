FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Sistem paketleri
RUN apt-get update && \
    apt-get install -y git git-lfs ffmpeg libsndfile1 && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# ÖNCE PIP'i GÜNCELLİYORUZ (Çözümleme sorunlarını giderir)
RUN python3 -m pip install --upgrade pip

# ADIM ADIM YÜKLEME (Döngüyü kırmak için)
# Önce sorun çıkaran 'typer' ve diğer temel paketleri kuruyoruz
RUN pip install --no-cache-dir "typer>=0.9.0" runpod soundfile

# Sonra resemble-enhance'i kuruyoruz
RUN pip install --no-cache-dir resemble-enhance

# Modelleri indirme
RUN python3 -c "from resemble_enhance.enhancer.inference import download; download()"

COPY handler.py /handler.py

CMD [ "python", "-u", "/handler.py" ]
