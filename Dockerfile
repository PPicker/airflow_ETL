FROM apache/airflow:2.8.3-python3.10


USER root

# 기본 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    chromium \
    ccache \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
USER airflow

# PyTorch CPU 버전 설치 (ARM64용)
RUN pip install --upgrade pip && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install 'transformers[torch]==4.42.4'
RUN pip install selenium bs4 pandas numpy google-genai streamlit \
    psycopg2-binary pgvector python-dotenv boto3


RUN pip install ultralytics
RUN pip install paddlepaddle paddleocr



# 프로젝트 파일 복사
COPY . .


