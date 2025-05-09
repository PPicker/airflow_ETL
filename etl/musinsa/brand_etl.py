from base.brand_etl import BaseBrandETL
from .platform_utils.brand_parser import get_brand_description
from config.env_loader import load_db_config
import requests
import os

import logging
logger = logging.getLogger(__name__)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/95.0.4638.69 Safari/537.36"
    )
}

class Musinsa_BrandETL(BaseBrandETL):

    def extract(self, brand_name: str, brand_url: str) -> dict:
        try:
            response = requests.get(brand_url, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        except Exception as e:
            logger.error(f"{brand_name} 페이지 요청 중 오류 발생: {e}")

        # brand description부터 추출
        name, description = get_brand_description(response, brand_name)

        brand_data = {"name": name, "url": brand_url, "description": description}
        return brand_data



if __name__ == "__main__":
    whitelist = load_whitelisted_brands()
    my_brands = whitelist["musinsa"]
    base_url = "https://www.musinsa.com"
    brand_dict = {brand: f"{base_url}/brand/{brand}" for brand in my_brands}
    etc_etl = Musinsa_BrandETL(
        brand_dict=brand_dict, platform="musinsa", db_config=load_db_config()
    )
    etc_etl.run()
