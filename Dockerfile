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


#모델 가중치 프리다운로드
#    → HuggingFace, YOLO, PaddleOCR 모델을 미리 받아 둡니다.
#    → 캐시 디렉터리(~/.cache) 안에 다운로드되므로, 런타임에 바로 로드 가능.
RUN python - <<EOF
from paddleocr import PaddleOCR
from ultralytics import YOLO
from transformers import YolosImageProcessor, AutoModelForObjectDetection

# 1) OCR 가중치
PaddleOCR(lang="korean")               

# 2) YOLOv8 가중치
YOLO('yolov8n.pt')                     

# 3) Fashionpedia 모델 가중치
YolosImageProcessor.from_pretrained(
    'valentinafeve/yolos-fashionpedia', trust_remote_code=True
)
AutoModelForObjectDetection.from_pretrained(
    'valentinafeve/yolos-fashionpedia'
)
EOF

# 프로젝트 파일 복사
COPY . .


