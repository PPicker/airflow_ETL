from datetime import datetime, timedelta
import json
import logging
import sys
from typing import Dict

from airflow import DAG
from airflow.decorators import task
from airflow.utils.trigger_rule import TriggerRule
from airflow.models import Variable

# ETL 모듈 경로 추가
sys.path.append('/opt/airflow/etl')
sys.path.append('/opt/airflow')

# ETL 클래스 임포트
from musinsa.brand_etl import Musinsa_BrandETL
from etcseoul.brand_etl import ETC_BrandETL
from musinsa.product_etl import Musinsa_ProductETL
from etcseoul.product_etl import ETC_ProductETL

# 로거 설정
logger = logging.getLogger(__name__)

def _create_single_brand_list(brands: Dict[str, str]) -> list[Dict[str, str]]:
    """
    {brand: url} 형태의 단일-키 딕셔너리 리스트로 변환
    """
    return [{brand: url} for brand, url in brands.items()]


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,                # 재시도 횟수를 0으로 설정
    # 'retry_delay': timedelta(minutes=5),  # 재시도 자체를 안 쓰면 이 라인은 지워도 됩니다
}

with DAG(
    dag_id='simplified_brand_etl',
    default_args=default_args,
    description='브랜드를 분류하고 각 플랫폼별 ETL 실행 (간소화 버전)',
    schedule_interval='0 1 * * *',  # 매일 오전 1시
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['brands', 'categorize', 'etl'],
) as dag:

    @task.branch
    def categorize_brands_and_decide() -> list[str] | str:
        """
        브랜드 URL을 분석하여 musinsa/ETC서울로 분류하고
        실행할 ETL 태스크 ID 리스트(또는 단일)를 리턴
        """
        brands_json = Variable.get("brand_dict", default_var="{}")
        brands_dict = json.loads(brands_json)

        if not brands_dict:
            logger.warning("'brand_dict' 변수가 비어 있거나 존재하지 않습니다.")
            return 'skip_etl'

        # 플랫폼별 분류
        musinsa_brands: Dict[str, str] = {}
        etcseoul_brands: Dict[str, str] = {}
        for brand, url in brands_dict.items():
            if 'musinsa.com' in url:
                musinsa_brands[brand] = url
            elif 'etcseoul.com' in url:
                etcseoul_brands[brand] = url

        # 변수 저장
        Variable.set("musinsa_brands", json.dumps(musinsa_brands))
        Variable.set("etcseoul_brands", json.dumps(etcseoul_brands))

        # 실행할 ETL 태스크 결정
        to_run: list[str] = []
        if musinsa_brands:
            to_run.append('run_musinsa_brand_etl')
        if etcseoul_brands:
            to_run.append('run_etcseoul_brand_etl')

        return to_run or 'skip_etl'

    @task
    def run_musinsa_brand_etl() ->list[Dict[str, str]]:
        """
        Musinsa 브랜드 ETL 실행 후 브랜드 딕셔너리 반환
        """
        musinsa_json = Variable.get("musinsa_brands", default_var="{}")
        brand_dict: Dict[str, str] = json.loads(musinsa_json)

        if not brand_dict:
            logger.warning("무신사 브랜드 정보가 없습니다.")
            return {}

        logger.info(f"무신사 ETL 시작: {len(brand_dict)}개 브랜드")
        Musinsa_BrandETL(brand_dict=brand_dict, platform="musinsa").run()
        logger.info("무신사 Brand ETL 완료")
        return _create_single_brand_list(brand_dict)

    @task(max_active_tis_per_dag=4)
    def run_musinsa_product_etl(single_brand: Dict[str, str]) -> bool:
        """
        Musinsa 플랫폼의 단일 브랜드 상품 ETL 실행
        """
        brand_name, url = next(iter(single_brand.items()))
        logger.info(f"무신사 Product ETL 시작: {brand_name}")
        Musinsa_ProductETL(brand_dict=single_brand, platform="musinsa").run()
        logger.info(f"무신사 {brand_name} 상품 ETL 완료")
        return True

    @task
    def run_etcseoul_brand_etl()  -> list[Dict[str, str]]:
        """
        ETC서울 브랜드 ETL 실행 후 브랜드 딕셔너리 반환
        """
        etc_json = Variable.get("etcseoul_brands", default_var="{}")
        brand_dict: Dict[str, str] = json.loads(etc_json)

        if not brand_dict:
            logger.warning("ETC서울 브랜드 정보가 없습니다.")
            return {}

        logger.info(f"ETC서울 ETL 시작: {len(brand_dict)}개 브랜드")
        ETC_BrandETL(brand_dict=brand_dict, platform="ETCSeoul").run()
        logger.info("ETC서울 Brand ETL 완료")

        return _create_single_brand_list(brand_dict)

    @task(max_active_tis_per_dag=4)
    def run_etcseoul_product_etl(single_brand: Dict[str, str]) -> bool:
        """
        ETC서울 플랫폼의 단일 브랜드 상품 ETL 실행
        """
        brand_name, url = next(iter(single_brand.items()))
        logger.info(f"ETC서울 Product ETL 시작: {brand_name}")
        ETC_ProductETL(brand_dict=single_brand, platform="ETCSeoul").run()
        logger.info(f"ETC서울 {brand_name} 상품 ETL 완료")
        return True

    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def skip_etl() -> bool:
        """
        실행할 ETL이 없을 때 호출되는 태스크
        """
        logger.info("실행할 ETL이 없습니다.")
        return True

    # DAG 흐름 정의
    decision = categorize_brands_and_decide()

    musinsa_brands = run_musinsa_brand_etl()
    etcseoul_brands = run_etcseoul_brand_etl()
    skipped = skip_etl()

    # Branch: decision 결과에 따라 실행
    decision >> [musinsa_brands, etcseoul_brands, skipped]

    # Brand ETL 완료 후 상품 ETL 매핑
    musinsa_products = run_musinsa_product_etl.expand(
        single_brand=musinsa_brands
    )
    etcseoul_products = run_etcseoul_product_etl.expand(
        single_brand=etcseoul_brands
    )

    # 명시적 체이닝: 브랜드 ETL → 상품 ETL
    musinsa_brands >> musinsa_products
    etcseoul_brands >> etcseoul_products
