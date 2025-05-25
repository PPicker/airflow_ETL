from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from .image_extractor import extract_images
from .detail_parser import parse_product_detail
from .. import headers,setup_driver
from selenium import webdriver
import logging


logger = logging.getLogger(__name__)


def json2dict(product_json):
    '''
    무신사 내부 meta 정보를 db에 맞춰서 수정
    '''
    return {
        "name": product_json.get("goodsName", ""),
        "brand": product_json.get("brand", ""),
        "category": product_json.get("category", None),
        "url": product_json.get("goodsLinkUrl", ""),
        "description_detail": "",
        "description_semantic": "",
        "description_semantic_raw": "",
        "original_price": product_json.get("normalPrice", None),
        "discounted_price": (
            product_json.get("price")
            if product_json.get("price") != product_json.get("normalPrice")
            else None
        ),
        "sold_out": product_json.get("isSoldOut", False),
        "thumbnail_url": product_json.get("thumbnail", ""),
    }


def parse_product_list(product_jsons):
    products = []
    driver = None
    max_retries = 3  # 최대 재시도 횟수

    i = 0
    while i < len(product_jsons):
        product_json = product_jsons[i]
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 드라이버가 없으면 새로 생성
                if driver is None:
                    driver = setup_driver()

                product = json2dict(product_json)
                try:
                    product["image_urls"] = extract_images(product["url"])
                except Exception as e:
                    logger.error(f"⚠️ 이미지 추출 실패 - {product.get('name', 'unknown')}: {str(e)}")
                    product["image_urls"] = []

                logger.info(
                    f"Processing: {product.get('name', 'unknown')} (시도 {retry_count+1}/{max_retries})"
                )

                description_txt, description_image_urls = parse_product_detail(
                    product["url"], driver
                )
                product["description_txt"] = description_txt
                product["description_image_urls"] = description_image_urls

                # 성공적으로 처리되면 제품 추가 및 내부 루프 탈출
                products.append(product)
                break

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"❌ 파싱 실패 - {product_json.get('name', 'unknown')} (시도 {retry_count}/{max_retries}): {str(e)}"
                )

                # 드라이버 재시작
                try:
                    driver.quit()
                except:
                    pass
                driver = setup_driver()

                # 최대 재시도 횟수에 도달하면
                if retry_count >= max_retries:
                    logger.error(
                        f"⚠️ 최대 재시도 횟수 초과 - {product_json.get('name', 'unknown')} 건너뜀"
                    )
                    # 빈 정보로 제품 추가 (선택사항)
                    product["description_txt"] = None
                    product["description_image_urls"] = []
                    products.append(product)

        # 다음 제품으로 이동
        i += 1

    # 마지막에 드라이버 종료
    if driver:
        try:
            driver.quit()
        except:
            pass

    return products
