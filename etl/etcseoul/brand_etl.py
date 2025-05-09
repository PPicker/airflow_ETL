from base.brand_etl import BaseBrandETL
from .platform_utils.brand_parser import get_brand_description
from config.env_loader import load_environment
import requests
import os
from utils.name_rule import normalize_brand_name
from . import headers


class ETC_BrandETL(BaseBrandETL):
    def extract(self, brand_name: str, brand_url: str) -> dict:
        try:
            response = requests.get(brand_url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        except Exception as e:
            print(f"{brand_name} 페이지 요청 중 오류 발생: {e}")

        # brand description부터 추출
        description = get_brand_description(response, brand_name)
        brand_data = {"name": brand_name, "url": brand_url, "description": description}
        return brand_data

