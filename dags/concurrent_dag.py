import time
import random
import socket
import os
from datetime import datetime, timedelta
import logging
from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator

# 로거 설정
logger = logging.getLogger(__name__)

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의
with DAG(
    'parallel_test_dag',
    default_args=default_args,
    description='병렬 처리 테스트용 DAG',
    schedule_interval=None,  # 수동 실행만 가능
    start_date=datetime(2025, 5, 1),
    catchup=False,
    tags=['test', 'parallel'],
) as dag:

    # 테스트 데이터 생성 함수
    @task
    def generate_test_data():
        """
        테스트용 데이터 생성
        """
        # 10개의 테스트 항목 생성
        test_items = []
        for i in range(1, 11):
            test_items.append({
                "id": i,
                "name": f"item_{i}",
                "process_time": random.randint(3, 10)  # 3-10초 랜덤 처리 시간
            })
        
        logger.info(f"테스트 데이터 {len(test_items)}개 생성 완료")
        return test_items

    # 병렬 처리 테스트 함수
    # @task
    @task(max_active_tis_per_dag=5)
    def process_item(item):
        """
        각 항목을 처리하는 함수 (병렬 실행)
        """
        item_id = item["id"]
        process_time = item["process_time"]
        hostname = socket.gethostname()
        pid = os.getpid()
        worker_id = f"{hostname}-{pid}"
        
        start_time = datetime.now()
        logger.info(f"[시작] 항목 {item_id} 처리 시작 - 워커: {worker_id}, 예상 처리 시간: {process_time}초")
        
        # 지정된 시간만큼 처리 시간 시뮬레이션
        time.sleep(process_time)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"[완료] 항목 {item_id} 처리 완료 - 워커: {worker_id}, 실제 처리 시간: {duration:.2f}초")
        
        return {
            "item_id": item_id,
            "worker": worker_id,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "duration": duration
        }
    
    # 결과 요약 함수
    @task
    def summarize_results(results):
        """
        처리 결과 요약
        """
        workers_used = set()
        total_duration = 0
        min_start_time = None
        max_end_time = None
        
        for result in results:
            workers_used.add(result["worker"])
            total_duration += result["duration"]
            
            start_time = datetime.strptime(result["start_time"], "%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.strptime(result["end_time"], "%Y-%m-%d %H:%M:%S.%f")
            
            if min_start_time is None or start_time < min_start_time:
                min_start_time = start_time
            
            if max_end_time is None or end_time > max_end_time:
                max_end_time = end_time
        
        actual_duration = (max_end_time - min_start_time).total_seconds()
        sequential_duration = total_duration
        speedup = sequential_duration / actual_duration if actual_duration > 0 else 0
        
        logger.info("=" * 50)
        logger.info("병렬 처리 결과 요약")
        logger.info("=" * 50)
        logger.info(f"처리된 항목 수: {len(results)}")
        logger.info(f"사용된 워커 수: {len(workers_used)}")
        logger.info(f"사용된 워커 목록: {', '.join(workers_used)}")
        logger.info(f"총 처리 시간(순차적): {sequential_duration:.2f}초")
        logger.info(f"총 처리 시간(병렬): {actual_duration:.2f}초")
        logger.info(f"속도 향상: {speedup:.2f}배")
        logger.info("=" * 50)
        
        return {
            "items_processed": len(results),
            "workers_used": len(workers_used),
            "sequential_duration": sequential_duration,
            "parallel_duration": actual_duration,
            "speedup": speedup
        }
    
    # 워크플로우 정의
    test_data = generate_test_data()
    process_results = process_item.expand(item=test_data)
    summary = summarize_results(process_results)