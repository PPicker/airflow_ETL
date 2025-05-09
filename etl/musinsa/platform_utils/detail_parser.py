from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def parse_product_detail(url, driver):

    driver.get(url)
    wait = WebDriverWait(driver, 30)
    button = wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                "button.gtm-click-button[data-button-id='prd_detail_open']",
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    driver.execute_script("arguments[0].click();", button)

    # 3. 컨텐츠 로드 대기: 클래스가 "text-xs font-normal text-black font-pretendard"인 모든 요소
    containers = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".text-xs.font-normal.text-black.font-pretendard")
        )
    )

    # 필요한 경우, 마지막 요소 대신 모든 요소를 순회할 수도 있음
    description_txt = ""  # 빈 str으로 넣어
    if text_content := containers[-1].text:
        description_txt = text_content

    """
    text가 없는 경우에만 image를 뽑도록 로직 조정
    """
    print("Text 형태로 저장되어있지 않습니다")
    description_image_urls = []
    for container_idx, container in enumerate(containers):
        imgs = container.find_elements(By.TAG_NAME, "img")
        for img_idx, img in enumerate(
            imgs[:-1]
        ):  # 마지막 하나를 제거해야함 why? ->배송, 제품 설명이 많음
            src = img.get_attribute("src")
            if src and (".jpg" in src.lower()):  # svg도 하고 싶으면 조건 확장 가능
                description_image_urls.append(src)

    return description_txt, description_image_urls
