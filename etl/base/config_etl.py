from config.env_loader import load_db_config, load_environment
from utils.aws import get_s3_client
import psycopg2

from utils.aws import get_s3_client
import psycopg2


class ETLBaseConfig:
    """
    ETL 실행에 필요한 공통 리소스를 제공하는 기반 클래스입니다.

    이 클래스는 데이터베이스 접속 설정과 S3 클라이언트를 관리합니다.
    dotenv 환경 변수는 외부에서 사전에 로드되었다고 가정하며,
    이 클래스 내부에서는 환경 변수만을 사용해 필요한 리소스를 구성합니다.

    이 구조를 선택한 이유는 다음과 같습니다:

    1. 단일 책임 원칙(SRP)을 따릅니다:
       - 환경 로딩(load_dotenv)은 실행 환경(main or CLI)에서 책임지도록 분리하고,
         이 클래스는 단순히 구성된 값을 사용만 합니다.

    2. 테스트 및 재사용이 용이합니다:
       - 다양한 환경에서 공통 리소스 구성 (DB/S3)을 반복 구현하지 않고 재사용할 수 있습니다.

    3. 확장성이 뛰어납니다:
       - 다른 ETL 클래스에서 상속받아 공통 리소스를 자동으로 사용할 수 있어
         ETL 구현체의 복잡도를 낮추고 유지보수를 간결하게 만듭니다.

    예: ProductETL, BrandETL 등은 이 클래스를 상속받아 DB/S3 접근을 일관되게 처리할 수 있습니다.
    """

    def __init__(self):
        self.db_config = load_db_config()
        self.s3_client = get_s3_client()

    def connect_to_db(self):
        return psycopg2.connect(**self.db_config)
