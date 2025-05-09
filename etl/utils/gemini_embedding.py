from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import numpy as np
import time
from typing import Dict


def to_natural_description(item: Dict[str, str]) -> str:
    """
    JSON → 자연어 서술형
    미리 정의한 템플릿에 꽂아넣어서 깔끔한 문장으로 만들어 줍니다.
    """
    template = (
        "{소재} 소재의 {세부_카테고리}입니다. "
        "{색상_및_패턴}이 포인트이며, "
        "{디테일}을 갖추어 "
        "{분위기_및_지향점}을 연출합니다. "
        "{실루엣} 실루엣으로 디자인되었습니다."
    )
    # 키 이름에 공백이나 특수문자가 있으면 사전에 바꿔둡니다.
    safe = {
        "세부_카테고리": item.get("세부 카테고리", ""),
        "소재": item.get("소재", ""),
        "색상_및_패턴": item.get("색상 및 패턴", ""),
        "디테일": item.get("디테일", ""),
        "분위기_및_지향점": item.get("분위기 및 지향점", ""),
        "실루엣": item.get("실루엣", ""),
    }
    return template.format(**safe).strip()


def to_tagged_description(item: Dict[str, str], sep: str = " | ") -> str:
    """
    JSON → 필드 태그 + 구분자
    각 속성을 "키: 값" 형태로 나열하고, 구분자(sep)로 연결합니다.
    """
    fields_order = [
        "소재",
        "장르",
        "디테일",
        "실루엣",
        "색상 및 패턴",
        "세부 카테고리",
        "분위기 및 지향점",
    ]
    parts = []
    for f in fields_order:
        v = item.get(f)
        if v:
            parts.append(f"{f}: {v}")
    return sep.join(parts)


class Gemini_Embedder:
    def __init__(self):
        self.tmp = 0
        self.api_keys = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GEMINI_API_KEY2"),
            os.getenv("GEMINI_API_KEY3"),
            os.getenv("GEMINI_API_KEY4"),
            os.getenv("GEMINI_API_KEY5"),
        ]
        self.client = genai.Client(
            api_key=self.api_keys[self.tmp],
        )
        self.wait_time = 10  # 대기 시간 (초)

    def embed(self, json_query):
        text_query = to_natural_description(json_query)
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = self.client.models.embed_content(
                    model="gemini-embedding-exp-03-07",
                    contents=text_query,
                    config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
                )
                embedding_np = np.array(result.embeddings[0].values, dtype=np.float32)
                emb_normalized = embedding_np / np.linalg.norm(embedding_np)
                return emb_normalized

            except Exception as e:
                print("재시도")
                time.sleep(self.wait_time)  # 10초 대기
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}")

                self.tmp = (self.tmp + 1) % 5
                self.client = genai.Client(
                    api_key=self.api_keys[self.tmp],
                )
        return None
