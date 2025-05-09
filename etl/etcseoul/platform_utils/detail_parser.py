from typing import Optional
import re


def parse_product_detail(soup: str) -> Optional[str]:
    wrap = soup.find("div", class_="detail_wrap")
    if not wrap:
        return None

    # 1) 태그 이름을 None 으로 두면, 모든 태그에서 style 속성만 보고 찾습니다.
    center_tags = wrap.find_all(None, style=re.compile(r"text-align\s*:\s*center"))
    if not center_tags:
        return None

    chunks = []
    for tag in center_tags:
        for node in tag.descendants:
            if node.name == "br":
                chunks.append("\n")
            elif isinstance(node, str):
                txt = node.strip()
                if txt:
                    chunks.append(txt)
        chunks.append("\n\n")

    full_text = "".join(chunks).strip()
    return full_text or None
