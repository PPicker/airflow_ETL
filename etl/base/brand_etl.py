from typing import Dict
from utils.name_rule import normalize_brand_name
from .config_etl import ETLBaseConfig


class BaseBrandETL(ETLBaseConfig):
    def __init__(self, brand_dict, platform="unknown"):
        super().__init__()
        '''
        brand_dict는 brand_name : url 형태의 dictionary임
        '''
        self.brand_dict = brand_dict
        self.platform = platform

    def extract(self, brand_name: str, brand_url: str) -> dict:
        raise NotImplementedError

    def transform(self, brand_data: dict) -> dict:
        # 정규화된 이름 추가
        brand_data["name_normalized"] = normalize_brand_name(brand_data["name"])
        return brand_data

    def load(self, brand_data: dict):
        query = """
        INSERT INTO brands (name, name_normalized, url, description, platform)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name, platform) DO UPDATE
        SET url = EXCLUDED.url,
            description = EXCLUDED.description,
            name_normalized = EXCLUDED.name_normalized;
        """
        values = (
            brand_data["name"],
            brand_data["name_normalized"],
            brand_data["url"],
            brand_data.get("description", ""),
            self.platform,
        )

        try:
            with self.connect_to_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, values)
                conn.commit()
            print(f"✅ 저장됨: {brand_data['name']} ({self.platform})")
        except Exception as e:
            print(f"❌ DB 저장 실패 - {brand_data['name']}: {e}")

    def run(self):
        for name, url in self.brand_dict.items():
            try:
                raw = self.extract(name, url)
                data = self.transform(raw)
                self.load(data)
            except Exception as e:
                print(f"❌ '{name}' 처리 실패: {e}")
