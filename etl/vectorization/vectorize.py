import os
import boto3
import psycopg2
import faiss
import numpy as np
from io import BytesIO
from PIL import Image
from utils.gemini_embedding import Gemini_Embedder
from config.env_loader import load_db_config, load_environment
from utils.aws import get_s3_client
from pgvector.psycopg2 import register_vector


class Vectorizer:
    """
    S3에서 이미지 로드 → 임베딩 생성 → FAISS 인덱스 갱신/검색 → PostgreSQL 메타 정보 조회
    """

    def __init__(self):
        # DB & S3 설정
        # AWS S3 클라이언트 생성
        load_environment()
        self.db_config = load_db_config()  # 여기서 load_dotenv가 불리는거였네
        self.s3_client = get_s3_client()
        # Embedding 모델 로드
        self.embedder = Gemini_Embedder()
        self.s3_bucket = os.getenv("AWS_S3_BUCKET_NAME")
        # self.conn = psycopg2.connect(**self.db_config)

    def embed_and_update(self):
        """
        products 테이블에서 is_embedded=False인 항목을 벡터화하여
        FAISS 인덱스에 추가하고, DB의 is_embedded 플래그를 True로 업데이트
        """
        # DB 연결
        conn = psycopg2.connect(**self.db_config)
        register_vector(conn)
        cur = conn.cursor()
        cur.execute("SELECT id, description FROM products WHERE embedding is NULL;")
        rows = cur.fetchall()
        if not rows:
            print("✅ 벡터화할 신규 상품이 없습니다.")
            conn.close()
            return
        for prod_id, description in rows:
            try:
                emb = self.embedder.embed(description)
                cur.execute(
                    """
                    UPDATE products
                    SET embedding = %s
                    WHERE id = %s
                    """,
                    (emb, prod_id),
                )
                conn.commit()
                print(f"ID {prod_id} 처리 완료")
            except Exception as e:
                print(f"❌ ID {prod_id} 처리 실패: {e}")
        conn.close()


if __name__ == "__main__":

    # .env 파일 로드

    vectorizer = Vectorizer()
    vectorizer.embed_and_update()
