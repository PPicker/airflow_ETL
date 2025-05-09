from bs4 import BeautifulSoup
import json


def get_brand_description(response, brand):
    html = response.text
    # 받아온 HTML을 BeautifulSoup으로 파싱
    soup = BeautifulSoup(html, "html.parser")

    # 예시: __NEXT_DATA__라는 id를 가진 스크립트 태그에서 JSON 데이터 추출
    next_data_script = soup.find("script", id="__NEXT_DATA__")

    json_text = next_data_script.string.strip()
    data = json.loads(json_text)
    # 페이지의 메타데이터 부분 추출 (예: props -> pageProps -> meta)
    brand_meta = data.get("props", {}).get("pageProps", {}).get("meta", {})
    brand_name = brand_meta["brandName"]
    brand_eng_name = brand_meta["brandNameEng"]
    description = brand_meta["introduction"]
    return f"{brand_name}({brand_eng_name})", description
