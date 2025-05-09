import os
import numpy as np
import psycopg2
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from .embedder import Embedding_Model  # 사용자 정의 임베딩 클래스
from utils.aws import get_s3_client
from config.env_loader import load_db_config, load_environment
from pgvector.psycopg2 import register_vector

if __name__ == "__main__":
    load_environment()
    db_config = load_db_config()
    embedder = Embedding_Model()
    conn = psycopg2.connect(**db_config)
    register_vector(conn)
    cur = conn.cursor()
    emb = embedder.embed_text("blue shirts").numpy().astype(np.float32)
    # cur.execute('SELECT * FROM products ORDER BY embedding <-> %s LIMIT 5', (emb,))
    cur.execute("SELECT * FROM products ORDER BY embedding <#> %s LIMIT 5", (emb,))

    rows = cur.fetchall()
    for row in rows:
        print(row)
