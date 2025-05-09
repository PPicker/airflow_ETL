from bs4 import BeautifulSoup

import logging

# 로거 설정
logger = logging.getLogger(__name__)

def get_brand_description(response, brand):
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # <map name="categoryhead_top_image_map_name"> 요소를 찾습니다.
    map_element = soup.find("map", {"name": "categoryhead_top_image_map_name"})
    if map_element:
        # 요소 내의 텍스트를 추출합니다.
        description = map_element.get_text(separator="\n").strip()
        return description
    else:
        logger.warning(f"{brand} 페이지에서 브랜드 설명 요소를 찾지 못했습니다.")
        # print(f"{brand} 페이지에서 브랜드 설명 요소를 찾지 못했습니다.")
        return None
