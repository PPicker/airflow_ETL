from transformers import AutoImageProcessor, AutoModelForObjectDetection
from PIL import Image
import torch
import os
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict
from transformers import YolosImageProcessor


class FashionDetector:
    # 패션 클래스 (Fashionpedia 기준)
    FASHION_CLASSES = [
        "shirt, blouse",
        "top, t-shirt, sweatshirt",
        "sweater",
        "cardigan",
        "jacket",
        "vest",
        "pants",
        "shorts",
        "skirt",
        "coat",
        "dress",
        "jumpsuit",
        "cape",
        "glasses",
        "hat",
        "headband, head covering, hair accessory",
        "tie",
        "glove",
        "watch",
        "belt",
        "leg warmer",
        "shoe",
        "bag, wallet",
        "scarf",
        "umbrella",
        "hood",
        "collar",
        "lapel",
        "epaulette",
        "sleeve",
        "pocket",
        "neckline",
        "buckle",
        "zipper",
        "applique",
        "bead",
        "bow",
        "flower",
        "fringe",
        "ribbon",
        "rivet",
        "ruffle",
        "sequin",
        "tassel",
    ]

    # 패션 카테고리 매핑
    CATEGORY_MAPPING = {
        "tops": [
            "shirt, blouse",
            "top, t-shirt, sweatshirt",
            "sweater",
            "vest",
            "jumpsuit",
            "dress",
        ],
        "bottoms": ["pants", "shorts"],
        "outerwear": ["jacket", "cardigan", "coat", "cape"],
        "shoes": ["shoe"],
        "accessories": [
            "glasses",
            "hat",
            "headband, head covering, hair accessory",
            "tie",
            "glove",
            "watch",
            "belt",
            "bag, wallet",
            "scarf",
            "umbrella",
        ],
    }

    def __init__(
        self,
        fashion_model_name="valentinafeve/yolos-fashionpedia",
        yolo_model_name="yolov8n.pt",
        person_threshold=0.35,
        fashion_threshold=0.3,
    ):
        # 패션 모델 로드
        # self.processor = AutoImageProcessor.from_pretrained(
        #     fashion_model_name, use_fast=True
        # )
        self.processor = YolosImageProcessor.from_pretrained(
            "valentinafeve/yolos-fashionpedia", trust_remote_code=True
        )

        self.fashion_model = AutoModelForObjectDetection.from_pretrained(
            fashion_model_name
        )
        self.person_threshold = person_threshold
        self.fashion_threshold = fashion_threshold

        # 사람 감지 모델 로드
        self.yolo_model = YOLO(yolo_model_name)

    @torch.inference_mode
    def detect_person(self, image: Image.Image) -> bool:
        """
        단일 이미지에서 사람이 있는지 감지합니다.

        Args:
            image: PIL.Image 객체

        Returns:
            의류만 있으면 True, 사람이 있으면 False
        """
        if image is None:
            return False

        result = self.yolo_model(
            image, conf=self.person_threshold, classes=[0], verbose=False
        )
        is_clothing_only = len(result[0].boxes) == 0

        return is_clothing_only

    @torch.inference_mode
    def batch_detect_person(
        self, images: List[Image.Image], batch_size: int = None
    ) -> List[bool]:
        """
        메모리에 있는 이미지 목록에서 사람이 있는지 감지하고 boolean 리스트를 반환합니다.

        Args:
            images: PIL.Image 객체 리스트
            batch_size: 한 번에 처리할 이미지 개수 (None이면 전체 이미지를 한 번에 처리)

        Returns:
            의류만 있으면 True, 사람이 있으면 False인 불리언 리스트
        """
        if not images:
            return []

        is_clothing_only_list = []

        # batch_size가 지정되지 않은 경우 모든 이미지를 한 번에 처리합니다.
        if batch_size is None:
            results = self.yolo_model(
                images, conf=self.person_threshold, classes=[0], verbose=False
            )
            is_clothing_only_list = [len(result.boxes) == 0 for result in results]
        else:
            # 지정된 batch_size 단위로 나누어 처리합니다.
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]
                results = self.yolo_model(
                    batch, conf=self.person_threshold, classes=[0], verbose=False
                )
                batch_flags = [len(result.boxes) == 0 for result in results]
                is_clothing_only_list.extend(batch_flags)

        return is_clothing_only_list

    @torch.inference_mode
    def detect_fashion(self, image: Image.Image) -> Dict:
        """
        단일 이미지에서 패션 아이템 감지

        Args:
            image: 처리할 이미지

        Returns:
            간소화된 결과 딕셔너리
        """
        if image is None:
            return {"is_fashion": False, "is_multi_category": False, "category": None}

        # 이미지를 리스트로 감싸서 프로세서에 전달
        inputs = self.processor(images=[image], return_tensors="pt")
        outputs = self.fashion_model(**inputs)

        # 결과 처리
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=self.fashion_threshold
        )[
            0
        ]  # 단일 이미지이므로 첫 번째 결과만 사용

        # 카테고리별 존재 여부 확인용 집합
        detected_labels = set()

        # 감지된 객체의 레이블만 수집
        for _, label, _ in zip(results["scores"], results["labels"], results["boxes"]):
            detected_labels.add(self.FASHION_CLASSES[label])

        # 카테고리별 존재 여부 확인
        has_tops = any(
            label in self.CATEGORY_MAPPING["tops"] for label in detected_labels
        )
        has_bottoms = any(
            label in self.CATEGORY_MAPPING["bottoms"] for label in detected_labels
        )
        has_outerwear = any(
            label in self.CATEGORY_MAPPING["outerwear"] for label in detected_labels
        )
        has_shoes = any(
            label in self.CATEGORY_MAPPING["shoes"] for label in detected_labels
        )
        has_accessories = any(
            label in self.CATEGORY_MAPPING["accessories"] for label in detected_labels
        )

        # 패션 아이템 존재 여부
        is_fashion = (
            has_tops or has_bottoms or has_outerwear or has_shoes or has_accessories
        )

        # 카테고리 결정
        category = None
        categories_found = []

        if has_tops:
            categories_found.append("top")
            category = "top"
        if has_bottoms:
            categories_found.append("bottom")
            category = "bottom"
        if has_outerwear:
            categories_found.append("outerwear")
            category = "outerwear"
        if has_shoes:
            categories_found.append("shoes")
            category = "shoes"
        if has_accessories:
            categories_found.append("accessories")
            category = "accessories"

        return {
            "is_fashion": is_fashion,
            "is_multi_category": len(categories_found) > 1,
            "category": category,
        }

    @torch.inference_mode
    def batch_detect_fashion(
        self, images: List[Image.Image], batch_size: int = None
    ) -> List[Dict]:
        """
        이미지 리스트를 배치로 처리하여 패션 아이템 감지

        Args:
            images: 처리할 이미지들
            batch_size: 한 번에 처리할 이미지 개수 (None이면 전체 이미지를 한 번에 처리)

        Returns:
            결과 딕셔너리 리스트
        """
        if not images:
            return []

        all_results = []

        # batch_size가 지정되지 않은 경우 모든 이미지를 한 번에 처리합니다.
        if batch_size is None:
            # 배치 추론 실행
            inputs = self.processor(images=images, return_tensors="pt")
            outputs = self.fashion_model(**inputs)

            # 결과 처리
            target_sizes = torch.tensor([img.size[::-1] for img in images])
            batch_results = self.processor.post_process_object_detection(
                outputs, target_sizes=target_sizes, threshold=self.fashion_threshold
            )

            # 전체 결과 반환
            for image_results in batch_results:
                # 각 카테고리별 존재 여부 확인용 집합
                detected_labels = set()

                # 감지된 객체의 레이블만 수집
                for _, label, _ in zip(
                    image_results["scores"],
                    image_results["labels"],
                    image_results["boxes"],
                ):
                    detected_labels.add(self.FASHION_CLASSES[label])

                # 카테고리별 존재 여부 확인
                has_tops = any(
                    label in self.CATEGORY_MAPPING["tops"] for label in detected_labels
                )
                has_bottoms = any(
                    label in self.CATEGORY_MAPPING["bottoms"]
                    for label in detected_labels
                )
                has_outerwear = any(
                    label in self.CATEGORY_MAPPING["outerwear"]
                    for label in detected_labels
                )
                has_shoes = any(
                    label in self.CATEGORY_MAPPING["shoes"] for label in detected_labels
                )
                has_accessories = any(
                    label in self.CATEGORY_MAPPING["accessories"]
                    for label in detected_labels
                )

                # 패션 아이템 존재 여부
                is_fashion = (
                    has_tops
                    or has_bottoms
                    or has_outerwear
                    or has_shoes
                    or has_accessories
                )

                # 카테고리 결정
                category = None
                categories_found = []

                if has_tops:
                    categories_found.append("top")
                    category = "top"
                if has_bottoms:
                    categories_found.append("bottom")
                    category = "bottom"
                if has_outerwear:
                    categories_found.append("outerwear")
                    category = "outerwear"
                if has_shoes:
                    categories_found.append("shoes")
                    category = "shoes"
                if has_accessories:
                    categories_found.append("accessories")
                    category = "accessories"

                all_results.append(
                    {
                        "is_fashion": is_fashion,
                        "is_multi_category": len(categories_found) > 1,
                        "category": category,
                    }
                )
        else:
            # 지정된 batch_size 단위로 나누어 처리합니다.
            for i in range(0, len(images), batch_size):
                batch = images[i : i + batch_size]

                # 배치 추론 실행
                inputs = self.processor(images=batch, return_tensors="pt")
                outputs = self.fashion_model(**inputs)

                # 결과 처리
                target_sizes = torch.tensor([img.size[::-1] for img in batch])
                batch_results = self.processor.post_process_object_detection(
                    outputs, target_sizes=target_sizes, threshold=self.fashion_threshold
                )

                # 각 이미지에 대한 결과 처리
                for image_results in batch_results:
                    # 각 카테고리별 존재 여부 확인용 집합
                    detected_labels = set()

                    # 감지된 객체의 레이블만 수집
                    for _, label, _ in zip(
                        image_results["scores"],
                        image_results["labels"],
                        image_results["boxes"],
                    ):
                        detected_labels.add(self.FASHION_CLASSES[label])

                    # 카테고리별 존재 여부 확인
                    has_tops = any(
                        label in self.CATEGORY_MAPPING["tops"]
                        for label in detected_labels
                    )
                    has_bottoms = any(
                        label in self.CATEGORY_MAPPING["bottoms"]
                        for label in detected_labels
                    )
                    has_outerwear = any(
                        label in self.CATEGORY_MAPPING["outerwear"]
                        for label in detected_labels
                    )
                    has_shoes = any(
                        label in self.CATEGORY_MAPPING["shoes"]
                        for label in detected_labels
                    )
                    has_accessories = any(
                        label in self.CATEGORY_MAPPING["accessories"]
                        for label in detected_labels
                    )

                    # 패션 아이템 존재 여부
                    is_fashion = (
                        has_tops
                        or has_bottoms
                        or has_outerwear
                        or has_shoes
                        or has_accessories
                    )

                    # 카테고리 결정
                    category = None
                    categories_found = []

                    if has_tops:
                        categories_found.append("top")
                        category = "top"
                    if has_bottoms:
                        categories_found.append("bottom")
                        category = "bottom"
                    if has_outerwear:
                        categories_found.append("outerwear")
                        category = "outerwear"
                    if has_shoes:
                        categories_found.append("shoes")
                        category = "shoes"
                    if has_accessories:
                        categories_found.append("accessories")
                        category = "accessories"

                    all_results.append(
                        {
                            "is_fashion": is_fashion,
                            "is_multi_category": len(categories_found) > 1,
                            "category": category,
                        }
                    )

        return all_results


if __name__ == "__main__":
    from PIL import Image

    image = Image.open("./test.jpg")
    detector = FashionDetector()
    # print(detector.detect_person(image))
    print(detector.detect_fashion(image))
