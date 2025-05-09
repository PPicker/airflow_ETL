from typing import List, Dict
import psycopg2
from utils.name_rule import normalize_product_name, normalize_brand_name
from .config_etl import ETLBaseConfig


class BaseProductETL(ETLBaseConfig):
    def __init__(self, brand_dict, platform="unknown"):
        super().__init__()
        self.brand_dict = brand_dict
        self.platform = platform

    def extract(self, brand_name, brand_url) -> List[dict]:
        """
        상품 목록 추출
        각 상품은 다음과 같은 dict 구조여야 함:
        {
            "name": str,
            "brand": str,
            "category": str,
            "url": str,
            "description_detail": str,
            "description_semantic": str,
            "price": int,
            "sold_out": bool,
            "image_urls": List[str]
        }
        """
        raise NotImplementedError

    def _transform_single_product(self, product: dict) -> dict:
        return product

    def transform(self, products):
        return [self._transform_single_product(product) for product in products]

    def transform_one(self, product):
        return self._transform_single_product(product)

    def _insert_product_and_images(self, cursor, p: dict):
        product_query = """
        INSERT INTO products
        (name, brand, brand_normalized, product_name_normalized, category, url,
        description_detail, description_semantic_raw, description_semantic,
        original_price, discounted_price, sold_out, thumbnail_key, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (name, brand) DO UPDATE
        SET
            category = EXCLUDED.category,
            url = EXCLUDED.url,
            description_detail = EXCLUDED.description_detail,
            description_semantic_raw = EXCLUDED.description_semantic_raw,
            description_semantic = EXCLUDED.description_semantic,
            original_price = EXCLUDED.original_price,
            discounted_price = EXCLUDED.discounted_price,
            sold_out = EXCLUDED.sold_out,
            thumbnail_key = EXCLUDED.thumbnail_key,
            updated_at = now()
        RETURNING id;
        """

        image_query = """
        INSERT INTO product_images (product_id, key, is_thumbnail, order_index, clothing_only)
        VALUES (%s, %s, %s, %s, %s);
        """

        cursor.execute(
            product_query,
            (
                p["name"],
                p["brand"],
                p["brand_normalized"],
                p["product_name_normalized"],
                p.get("category", None),
                p["url"],
                p.get("description_detail", ""),
                p.get("description_semantic_raw", ""),
                p.get("description_semantic", ""),
                p.get("original_price"),
                p.get("discounted_price"),
                p["sold_out"],
                p.get("thumbnail_key", None),  # 여기에 thumbnail_key 추가
            ),
        )

        product_id = cursor.fetchone()[0]

        for entry in p.get("image_entries", []):
            cursor.execute(
                image_query,
                (
                    product_id,
                    entry["key"],
                    entry["is_thumbnail"],
                    entry["order_index"],
                    entry["clothing_only"],
                ),
            )

    def load(self, products: List[dict]):
        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    for p in products:
                        self._insert_product_and_images(cursor, p)
                conn.commit()
            print(f"✅ 상품 {len(products)}개 및 이미지 저장 완료: {self.platform}")
        except Exception as e:
            print(f"❌ 상품 저장 실패 ({self.platform}): {e}")

    def load_one(self, p: dict):
        """
        안정성을 위해 하나씩 transform 후 하나씩 load
        """
        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    self._insert_product_and_images(cursor, p)
                conn.commit()
            print(f"✅ 저장 완료: {p['name']} ({self.platform})")
        except Exception as e:
            print(
                f"❌ 저장 실패 - 상품명: {p.get('name', 'UNKNOWN')} / 브랜드: {p.get('brand', 'UNKNOWN')} - 오류: {e}"
            )

    def run(self, single=True):
        """
        default를 one으로 줘야한다.
        """
        for brand_name, brand_url in self.brand_dict.items():
            try:
                raw_products = self.extract(brand_name, brand_url)
                if single:
                    for product in raw_products:

                        try:
                            product = self.transform_one(product)
                            self.load_one(product)
                        except Exception as e:
                            print(f"❌ 제품 실패 - {product['name']}: {e}")
                else:
                    try:
                        products = self.transform(raw_products)
                        self.load(products)
                    except Exception as e:
                        print(f"❌ 일괄 처리 실패 - {brand_name}: {e}")

            except Exception as e:
                print(f"❌ 브랜드 실패 - {brand_name}: {e}")
