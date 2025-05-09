from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from .price_parser import extract_price
from .image_extractor import extract_images
from .detail_parser import parse_product_detail
from .. import headers, base_url

import logging
# 로거 설정
logger = logging.getLogger(__name__)


def parse_product_list(response, brand=None):
    soup = BeautifulSoup(response.text, "html.parser")
    products = []
    for item in soup.select("li.item.xans-record-"):
        a_tag = item.select_one("a.name")
        if not a_tag:
            continue

        product_name = (
            a_tag.get_text(strip=True).replace(":", "").strip()
        )  # 없애 갑자기 이게 붙네 왜지???
        product_href = urljoin(base_url, a_tag.get("href"))

        price_info_block = item.select_one("ul.xans-product-listitem")
        if price_info_block:
            price_text = price_info_block.get_text(" ", strip=True)
            if "원" not in price_text:
                continue

            original_price, discounted_price = extract_price(price_text)
            if not original_price:
                continue
        try:
            detail_response = requests.get(product_href, headers=headers)
            soup = BeautifulSoup(detail_response.text, "html.parser")

            product_detail = parse_product_detail(soup)
            image_urls = extract_images(soup)
            products.append(
                {
                    "name": product_name,
                    "brand": brand,
                    "category": None,  # 필요 시 분류
                    "url": product_href,
                    "description_detail": "",
                    "description_semantic": "",
                    "description_semantic_raw": (
                        product_detail if product_detail else ""
                    ),
                    "original_price": int(
                        original_price.replace(",", "").replace("원", "")
                    ),  # 아직 할인 옵션 추가 X
                    "discounted_price": (
                        int(discounted_price.replace(",", "").replace("원", ""))
                        if discounted_price
                        else None
                    ),  # 아직 할인 옵션 추가 X
                    "sold_out": False,
                    "image_urls": image_urls,
                }
            )

        except Exception as e:
            logger.error(f"❌ 상세 페이지 처리 실패: {product_href}, 오류: {e}")
            continue

    return products
