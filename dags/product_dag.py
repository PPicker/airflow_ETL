from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import json
import os
import sys
import logging

# ETL 모듈의 경로 추가
sys.path.append('/opt/airflow/etl')
sys.path.append('/opt/airflow')

# 필요한 모듈 임포트
from base.product_etl import BaseProductETL
from musinsa.product_etl import Musinsa_ProductETL
from etcseoul.product_etl import Etcseoul_ProductETL
from config.env_loader import load_environment

# 로거 설정
logger = logging.getLogger(__name__)

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'product_etl',
    default_args=default_args,
    description='product etl 호출 (Airflow Variables 활용)',
    schedule_interval='0 1 * * *',  # 매일 오전 1시에 실행
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['fashion', 'ecommerce', 'product_etl', 'etl'],
)

# 환경 변수 로드 함수
def load_env_vars(**kwargs):
    """
    환경 변수 로드 및 Airflow Variables 초기화
    """
    # 환경 변수 로드
    load_environment()
    
    # 브랜드 변수 존재 여부 확인
    try:
        musinsa_brands_json = Variable.get("musinsa_brands", default_var=None)
        if musinsa_brands_json is None:
            # 기본 무신사 브랜드 설정
            default_musinsa = ["bronson"]
            Variable.set("musinsa_brands", json.dumps(default_musinsa))
            logger.info("무신사 브랜드 목록 초기화: %s", default_musinsa)
        
        etcseoul_brands_json = Variable.get("etcseoul_brands", default_var=None)
        if etcseoul_brands_json is None:
            # 기본 ETC서울 브랜드 설정
            default_etcseoul = ["Art if acts", "TONYWACK", "OURSELVES", "ROUGH SIDE", "SHRITER", "MFPEN"]
            Variable.set("etcseoul_brands", json.dumps(default_etcseoul))
            logger.info("ETC서울 브랜드 목록 초기화: %s", default_etcseoul)
    except Exception as e:
        logger.error("변수 초기화 중 오류 발생: %s", str(e))
        raise
    
    return True

# 무신사 ETL 실행 함수
def run_musinsa_etl(**kwargs):
    """
    무신사 ETL 클래스를 사용하여 ETL 파이프라인 실행
    """
    try:
        # Airflow Variables에서 브랜드 목록 가져오기
        brands_json = Variable.get("musinsa_brands", default_var="[]")
        brands = json.loads(brands_json)
        
        if not brands:
            logger.warning("처리할 무신사 브랜드가 없습니다.")
            return 0
        
        # 브랜드 URL 생성
        base_url = "https://www.musinsa.com"
        brand_dict = {brand: f"{base_url}/brand/{brand}" for brand in brands}
        
        logger.info("무신사 ETL 시작: %s", list(brand_dict.keys()))
        
        # ETL 객체 생성 (BaseProductETL 상속 클래스)
        etl = Musinsa_ProductETL(brand_dict=brand_dict, platform="musinsa")
        
        # 각 단계별로 실행 - 클래스의 메서드 사용
        extracted_products = []
        for brand_name, brand_url in brand_dict.items():
            products = etl.extract(brand_name=brand_name, brand_url=brand_url)
            extracted_products.extend(products)
        
        logger.info(f"추출된 무신사 제품: {len(extracted_products)}개")
        
        # 변환 단계
        transformed_products = []
        for product in extracted_products:
            transformed_product = etl._transform_single_product(product)
            transformed_products.append(transformed_product)
        
        logger.info(f"변환된 무신사 제품: {len(transformed_products)}개")
        
        # 적재 단계
        etl.load(transformed_products)
        logger.info(f"적재된 무신사 제품: {len(transformed_products)}개")
        
        return len(transformed_products)
    except Exception as e:
        logger.error("무신사 ETL 실행 중 오류 발생: %s", str(e))
        raise

# ETC서울 ETL 실행 함수
def run_etcseoul_etl(**kwargs):
    """
    ETC서울 ETL 클래스를 사용하여 ETL 파이프라인 실행
    """
    try:
        # Airflow Variables에서 브랜드 목록 가져오기
        brands_json = Variable.get("etcseoul_brands", default_var="[]")
        brands = json.loads(brands_json)
        
        if not brands:
            logger.warning("처리할 ETC서울 브랜드가 없습니다.")
            return 0
        
        # 브랜드 URL 생성
        base_url = "https://www.etcseoul.com"
        brand_dict = {brand: f"{base_url}/{brand.replace(' ', '-')}" for brand in brands}
        
        logger.info("ETC서울 ETL 시작: %s", list(brand_dict.keys()))
        
        # ETL 객체 생성 (BaseProductETL 상속 클래스)
        etl = Etcseoul_ProductETL(brand_dict=brand_dict, platform="etcseoul")
        
        # 각 단계별로 실행 - 클래스의 메서드 사용
        extracted_products = []
        for brand_name, brand_url in brand_dict.items():
            products = etl.extract(brand_name=brand_name, brand_url=brand_url)
            extracted_products.extend(products)
        
        logger.info(f"추출된 ETC서울 제품: {len(extracted_products)}개")
        
        # 변환 단계
        transformed_products = []
        for product in extracted_products:
            transformed_product = etl._transform_single_product(product)
            transformed_products.append(transformed_product)
        
        logger.info(f"변환된 ETC서울 제품: {len(transformed_products)}개")
        
        # 적재 단계
        etl.load(transformed_products)
        logger.info(f"적재된 ETC서울 제품: {len(transformed_products)}개")
        
        return len(transformed_products)
    except Exception as e:
        logger.error("ETC서울 ETL 실행 중 오류 발생: %s", str(e))
        raise

# 태스크 정의
load_env_task = PythonOperator(
    task_id='load_environment',
    python_callable=load_env_vars,
    dag=dag,
)

musinsa_task = PythonOperator(
    task_id='run_musinsa_etl',
    python_callable=run_musinsa_etl,
    dag=dag,
)

etcseoul_task = PythonOperator(
    task_id='run_etcseoul_etl',
    python_callable=run_etcseoul_etl,
    dag=dag,
)

# 태스크 의존성 설정
load_env_task >> [musinsa_task, etcseoul_task]