import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
from .. import base_url, headers
import os
import re
import json
import logging
logger = logging.getLogger(__name__)

def get_normalized_image_format_from_url(url):
    """
    이미지 URL에서 확장자를 추출하고, Pillow 및 Content-Type에서 사용 가능한 형식으로 정규화한다.
    """
    path = urlparse(url).path
    ext = os.path.splitext(path)[-1].lower().strip(".")

    format_map = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "gif": "GIF",
        "bmp": "BMP",
        "tiff": "TIFF",
    }

    normalized_format = format_map.get(ext, "JPEG")  # 확장자가 없거나 예상 못 하면 기본 'JPEG'
    if ext and ext not in format_map:
        logger.warning(f"알 수 없는 이미지 확장자: {ext}, 기본값 'JPEG'로 설정합니다. URL: {url}")
    

    return normalized_format

def extract_images(url):
    """
    지정한 URL의 HTML에서 src 속성에 '/web/upload/NNEditor/'가 포함된 <img> 태그의 절대 URL을 리스트로 반환합니다.
    """

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # ✅ soup 전체 HTML 문자열로 변환

    images = []

    # window.__MSS__.product.state에서 goodsImages 데이터 찾기
    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string and "goodsImages" in script.string:
            # JSON 데이터 추출
            json_match = re.search(
                r"window\.__MSS__\.product\.state\s*=\s*({.*?});",
                script.string,
                re.DOTALL,
            )
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    if "goodsImages" in json_data:
                        for img in json_data["goodsImages"]:
                            # 상대 URL을 절대 URL로 변환
                            full_url = f"https://image.msscdn.net{img['imageUrl']}"
                            images.append(full_url)
                except json.JSONDecodeError:
                    logger.error("JSON 파싱 오류 발생")

    # 방법 2: 정규식으로 직접 추출 (대체 방법)
    if not images:
        # goodsImages 배열에서 imageUrl 추출
        image_urls = re.findall(r'"imageUrl":"(\/images\/prd_img\/.*?)"', response.text)
        for i, url in enumerate(image_urls):
            full_url = f"https://image.msscdn.net{url}"
            images.append(full_url)
    return images


def load_image_from_url(url):
    """
    URL에서 이미지를 다운로드하여 PIL Image로 변환

    Args:
        url: 이미지 URL

    Returns:
        PIL Image 객체
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # HTTP 오류 확인
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        raise ValueError(
            f"이미지 URL을 로드하는 중 오류가 발생했습니다: {url}, 오류: {str(e)}"
        )


def upload_pil_image_to_s3(pil_image, filename, bucket, s3_client, format="JPEG"):
    try:
        img_buffer = BytesIO()
        pil_image.save(img_buffer, format=format)
        img_buffer.seek(0)
        s3_client.put_object(
            Bucket=bucket,
            Key=filename,
            Body=img_buffer,
            ContentType=f"image/{format.lower()}",
        )

        s3_url = f"https://{bucket}.s3.amazonaws.com/{filename}"
        return s3_url
    except Exception as e:
        logger.error(f"❌ S3 업로드 실패: {filename}, 오류: {e}")
        return None


# if __name__ == '__main__':
#     import requests
#     from bs4 import BeautifulSoup
#     import re
#     import json
#     # ✅ 크롤링할 URL


#     url = "https://www.musinsa.com/products/3836510"
#     headers = {
#         "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#                        "AppleWebKit/537.36 (KHTML, like Gecko) "
#                        "Chrome/95.0.4638.69 Safari/537.36")
#     }

#     # ✅ HTML 요청 및 soup 파싱
#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.text, "html.parser")

#     # ✅ soup 전체 HTML 문자열로 변환


#     images = []

#     # window.__MSS__.product.state에서 goodsImages 데이터 찾기
#     script_tags = soup.find_all('script')
#     for script in script_tags:
#         if script.string and "goodsImages" in script.string:
#             # JSON 데이터 추출
#             json_match = re.search(r'window\.__MSS__\.product\.state\s*=\s*({.*?});', script.string, re.DOTALL)
#             if json_match:
#                 try:
#                     json_data = json.loads(json_match.group(1))
#                     if 'goodsImages' in json_data:
#                         for img in json_data['goodsImages']:
#                             # 상대 URL을 절대 URL로 변환
#                             full_url = f"https://image.msscdn.net{img['imageUrl']}"
#                             images.append({
#                                 'seq': img['seq'],
#                                 'url': full_url
#                             })
#                 except json.JSONDecodeError:
#                     print("JSON 파싱 오류 발생")

#     # 방법 2: 정규식으로 직접 추출 (대체 방법)
#     if not images:
#         # goodsImages 배열에서 imageUrl 추출
#         image_urls = re.findall(r'"imageUrl":"(\/images\/prd_img\/.*?)"', response.text)
#         for i, url in enumerate(image_urls):
#             full_url = f"https://image.msscdn.net{url}"
#             images.append({
#                 'seq': i+1,
#                 'url': full_url
#             })
#     print(images)
