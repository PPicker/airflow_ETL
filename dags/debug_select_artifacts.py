# dags/debug_select_artifacts.py
from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
import os 

with DAG(
    dag_id="debug_select_artifacts",
    start_date=datetime(2025, 5, 2),
    schedule=None,          # 수동으로만 실행
    catchup=False,
    tags=["debug", "quick"],
):
    @task
    def test_db():
        print("got okay??")
        try:
            CONN_ID = os.getenv("PRODUCTS_CONN_ID", "postgres_ppicker")
            print(f"🔍 연결 ID: {CONN_ID}")
            
            hook = PostgresHook(postgres_conn_id=CONN_ID)
            result = hook.get_first("SELECT 1 AS test")
            print(f"🟢 연결 성공! 결과: {result}")
            return True
        except Exception as e:
            print(f"🔴 오류: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    test_db()