import os
import argparse
from dotenv import load_dotenv


def load_environment():
    """
    argparse에 맞춰서 load하도록
    안정성을 위해서 default는 test로 잡아놓음
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=".env.test", help="환경변수 파일 경로")
    args = parser.parse_args()
    load_dotenv(dotenv_path=args.env)


def load_db_config():
    """
    지정된 .env 파일을 로드하고, DB 설정 딕셔너리 반환
    load_dotenv는 외부에서 실행되어있음을 가정 -> test/prod를 완벽하게 쪼개기 위함
    """

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
