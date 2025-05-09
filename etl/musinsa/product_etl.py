from base.product_etl import BaseProductETL
import requests
import os
from typing import List
import numpy as np
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from . import headers, base_url
from .platform_utils.product_parser import parse_product_list
from .platform_utils.image_extractor import (
    load_image_from_url,
    upload_pil_image_to_s3,
    get_normalized_image_format_from_url,
)
from config.brand_whitelist_loader import load_whitelisted_brands
from config.env_loader import load_db_config, load_environment
from .get_brand_url import load_brand_dict_from_csv
from utils.fashion_detector import FashionDetector
from utils.ocr import OCR
from utils.name_rule import normalize_product_name, normalize_brand_name, get_image_name
import uuid

import logging

logger = logging.getlogger(__name__)

class Musinsa_ProductETL(BaseProductETL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 부모 클래스 초기화
        self.fashion_detector = FashionDetector()  # 추가 속성 초기화
        self.ocr = OCR()

    def extract(self, brand_name, brand_url) -> List[dict]:
        product_base_url = "https://api.musinsa.com/api2/dp/v1/plp/goods"
        params = {
            "brand": f"{brand_name}",  # 원하는 브랜드
            "sortCode": "POPULAR",
            "page": 1,  # 시작 페이지 번호
            "size": 30,  # 한 페이지당 제품 수
            "caller": "FLAGSHIP",
            "gf": "M",  # 성별 남자 , 여성은 F, 전체는 A임
            "category": "001",  # 001 : 상의, 002 : 아우터, 003 : 하의
        }

        category_dicts = {"001": "TOP", "002": "OUTER", "003": "BOTTOM"}
        try:
            products_data = []
            products = []
            for key, value in category_dicts.items():
                params["page"] = 1  # 초기화해줌
                params["category"] = key
                while True:
                    # API 요청 보내기
                    response = requests.get(
                        product_base_url, params=params, headers=headers
                    )
                    json_data = response.json()
                    # 제품 데이터는 data.list 에 있음
                    tmp_products = json_data.get("data", {}).get("list", [])
                    tmp_products = [
                        {**product, "category": value} for product in tmp_products
                    ]  # category 추가

                    products.extend(tmp_products)  # 일단 10개로 고정
                    pagination = json_data.get("data", {}).get("pagination", {})
                    has_next = pagination.get("hasNext", False)
                    has_next = False  # 일단 페이지 넘기지 마
                    logger.info(
                        f"페이지 {params['page']}에서 {len(tmp_products)}개의 제품 수집"
                    )

                    # 다음 페이지가 없으면 종료
                    if not has_next:
                        logger.info("더 이상 페이지가 없습니다. 종료합니다.")
                        break
                    params["page"] += 1
        except Exception as e:
            logger.error(f"{brand_name} 페이지 요청 중 오류 발생: {e}")

        return parse_product_list(products)

    def _transform_single_product(self, product: dict) -> dict:

        description_image_urls = product["description_image_urls"]
        description_images = [
            load_image_from_url(image_url) for image_url in description_image_urls
        ]
        # detector = FashionDetector()
        is_clothing_list = self.fashion_detector.batch_detect_person(
            description_images, batch_size=4
        )
        all_results = self.fashion_detector.batch_detect_fashion(
            description_images, batch_size=4
        )

        is_fashion_list = [result["is_fashion"] for result in all_results]

        # OCR 결과를 모으는 리스트
        description_raw_list = []

        # 각 이미지를 순회하며 조건에 맞는 이미지에 OCR 실행
        for idx, (is_clothing, is_fashion, description_image) in enumerate(
            zip(is_clothing_list, is_fashion_list, description_images)
        ):
            # 의류도 아니고 패션도 아닐 때만 OCR 실행
            if is_clothing and not is_fashion:
                description_image_array = np.array(description_image)
                description_list = self.ocr.run_ocr(
                    description_image_array
                )  # paddle ocr은 PIL.Image를 못받음
                # OCR 결과(문자열 리스트)를 전체 리스트에 추가
                description_raw_list.append(" ".join(description_list))
        # OCR 결과가 있는 경우에만 기존 텍스트 업데이트 또는 추가
        description_semantic_raw = product["description_txt"] + "\n"  # base
        for description_raw in description_raw_list:
            description_semantic_raw = (
                description_semantic_raw + description_raw + "\n"
            )  # 줄바꿈으로 추가
        product["description_semantic_raw"] = description_semantic_raw

        """
        image urls + thumbnail url처리해줘야함
        """

        product["product_name_normalized"] = normalize_product_name(product["name"])
        product["brand_normalized"] = normalize_brand_name(product["brand"])
        s3_image_path_base = get_image_name(
            platform=self.platform,
            brand=product["brand_normalized"],
            product_name=product["product_name_normalized"],
        )

        image_entries = []
        thumbnail_entry = {}
        thumbnail_url = product["thumbnail_url"]
        thumbnail_image = load_image_from_url(thumbnail_url)

        """
        entry["url"],
                entry["is_thumbnail"],
                entry["order_index"], 
                entry["clothing_only"]
        """
        thumbnail_entry["is_thumbnail"] = True
        thumbnail_entry["order_index"] = 0
        thumbnail_entry["clothing_only"] = True
        image_format = get_normalized_image_format_from_url(thumbnail_url)
        s3_image_path = s3_image_path_base + f"{uuid.uuid4()}"
        if s3_url := upload_pil_image_to_s3(
            thumbnail_image,
            s3_image_path,
            "ppicker",
            self.s3_client,
            format=image_format,
        ):
            thumbnail_entry["key"] = s3_image_path
            product["thumbnail_key"] = s3_image_path
            image_entries.append(thumbnail_entry)

        for idx, image_url in enumerate(product["image_urls"]):
            tmp_entry = {"is_thumbnail": False, "order_index": idx + 1}
            image_format = get_normalized_image_format_from_url(image_url)
            image = load_image_from_url(image_url)
            tmp_entry["clothing_only"] = self.fashion_detector.detect_person(image)
            s3_image_path = s3_image_path_base + f"{uuid.uuid4()}"
            if s3_url := upload_pil_image_to_s3(
                image, s3_image_path, "ppicker", self.s3_client, format=image_format
            ):
                tmp_entry["key"] = s3_image_path
                image_entries.append(thumbnail_entry)
        product["image_entries"] = image_entries
        return product

