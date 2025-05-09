import re
import os


def normalize_brand_name(name: str) -> str:
    """공백을 언더스코어(_)로 변환하고, 특수문자 제거."""
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_가-힣]", "", name)
    return name


def normalize_product_name(name: str) -> str:
    """공백을 언더스코어(_)로 변환하고, 특수문자 제거."""
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_가-힣]", "", name)
    return name


def get_image_name(platform: str, brand: str, product_name: str) -> str:
    return os.path.join(platform, brand, product_name)
