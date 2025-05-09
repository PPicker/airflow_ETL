import re
from bs4 import BeautifulSoup

price_pattern = r"\s*:\s*(\d{1,3}(?:,\d{3})*원)(?:\s*:\s*(\d{1,3}(?:,\d{3})*원))?"


def extract_price(price_text):
    match = re.search(price_pattern, price_text)
    if match:
        original = match.group(1)
        discounted = match.group(2)
        return original, discounted or None
    return None, None


# def extract_price(soup):

#     original_price = soup.find(id="span_product_price_text").get_text(strip=True)

#     # 세일가(없을 수도 있음)
#     price_sale_tag = soup.find(id="span_product_price_sale")
#     discounted_price = price_sale_tag.get_text(strip=True) if price_sale_tag else None
#     return original_price,discounted_price
