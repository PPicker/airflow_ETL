import json
import os


def load_whitelisted_brands(json_path: str = None):
    """
    플랫폼별 허용된 브랜드 목록을 JSON에서 로드
    """
    if not json_path:
        json_path = os.path.join(os.path.dirname(__file__), "brand_whitelist.json")

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
