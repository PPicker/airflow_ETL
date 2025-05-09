from paddleocr import PaddleOCR
from typing import List


class OCR:
    def __init__(self, lang: str = "korean", **kwargs):
        self.lang = lang
        self._ocr = PaddleOCR(lang="korean")
        self.img_path = None
        self.ocr_result = {}

    def run_ocr(self, img_path: str) -> List:
        self.img_path = img_path
        ocr_text = []
        result = self._ocr.ocr(img_path, cls=False)
        self.ocr_result = result[0]

        if self.ocr_result:
            for r in result[0]:
                ocr_text.append(r[1][0])
        return ocr_text

    def check_txt_exists(self, img_path: str):
        """
        no batch inference supported
        """
        if self._ocr.ocr(img_path, rec=False, cls=False)[0]:  # result가 있는경우
            return True
        else:
            return False


if __name__ == "__main__":
    ocr = OCR()
    print(ocr.check_txt_exists("KakaoTalk_Photo_2025-02-10-15-16-11.png"))
    print(ocr.run_ocr("6.png"))
