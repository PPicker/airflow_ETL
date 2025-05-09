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

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
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
    def categorize_brands_and_decide():
        """
        브랜드 URL을 분석하여 musinsa/ETC서울로 분류하고
        실행할 ETL 태스크 ID를 리턴합니다.
        """
        brands_json = Variable.get("brand_dict", default_var="{}")
        brands_dict = json.loads(brands_json)

        if not brands_dict:
            logger.warning("'brand_dict' 변수가 비어 있거나 존재하지 않습니다.")
            return "skip_etl"

        musinsa_brands = {}
        etc_brands = {}
        for brand, url in brands_dict.items():
            if "musinsa.com" in url:
                musinsa_brands[brand] = url
            elif "etcseoul.com" in url:
                etc_brands[brand] = url

        Variable.set("musinsa_brands", json.dumps(musinsa_brands))
        Variable.set("etcseoul_brands", json.dumps(etc_brands))

        to_run = []
        if musinsa_brands:
            to_run.append("run_musinsa_brand_etl")
        if etc_brands:
            to_run.append("run_etcseoul_brand_etl")

        return to_run or "skip_etl"

    @task
    def run_musinsa_brand_etl():
        musinsa_json = Variable.get("musinsa_brands", default_var="{}")
        brand_dict = json.loads(musinsa_json)
        if not brand_dict:
            logger.warning("무신사 브랜드 정보가 없습니다.")
            return None

        logger.info(f"무신사 ETL 시작: {len(brand_dict)}개 브랜드")
        Musinsa_BrandETL(brand_dict=brand_dict, platform="musinsa").run()
        logger.info("무신사 Brand ETL 완료")
        return brand_dict

    
    @task
    def run_musinsa_product_etl(single_brand_dict:Dict):
        logger.info(f"무신사 Product ETL 시작 : {single_brand_dict.keys()[0]}")
        Musinsa_BrandETL(brand_dict=brand_dict, platform="musinsa").run()
        logger.info("무신사 Brand ETL 완료")
        return brand_dict


    @task
    def run_etcseoul_brand_etl():
        etc_json = Variable.get("etcseoul_brands", default_var="{}")
        brand_dict = json.loads(etc_json)
        if not brand_dict:
            logger.warning("ETC서울 브랜드 정보가 없습니다.")
            return 0

        logger.info(f"ETC서울 ETL 시작: {len(brand_dict)}개 브랜드")
        ETC_BrandETL(brand_dict=brand_dict, platform="etcseoul").run()
        logger.info("ETC서울 Brand ETL 완료")
        return brand_dict

    


    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def skip_etl():
        logger.info("실행할 ETL이 없습니다.")
        return True

    # 실행 순서 정의
    decision = categorize_brands_and_decide()
    musinsa      = run_musinsa_brand_etl()
    etcseoul     = run_etcseoul_brand_etl()
    skipped      = skip_etl()

    # Branching
    decision >> [musinsa, etcseoul, skipped]