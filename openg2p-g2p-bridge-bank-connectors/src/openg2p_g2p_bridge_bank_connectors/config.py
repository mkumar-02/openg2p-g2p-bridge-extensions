from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="g2p_bridge_bank_connectors_", env_file=".env", extra="allow"
    )

    db_dbname: str = "openg2p_g2p_bridge_db"

    funds_available_check_url_example_bank: str = (
        "https://example-bank.dev.openg2p.org/api/example-bank/check_funds"
    )
    funds_block_url_example_bank: str = "https://example-bank.dev.openg2p.org/api/example-bank/block_funds"
    funds_disbursement_url_example_bank: str = (
        "https://example-bank.dev.openg2p.org/api/example-bank/initiate_payment"
    )
    bank_simulator_code: str = "ZAMBIA"

    # Registry database connection settings for g2p_worker_registry
    db_driver_registry: str = "postgresql"
    db_username_registry: str = "postgres"
    db_password_registry: str = "postgres"
    db_hostname_registry: str = "localhost"
    db_port_registry: int = 5432
    db_dbname_registry: str = "registrydb"

    # Minio configuration for Zambia CSV Connector
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "zambia-csv-files"
    minio_secure: bool = False
    minio_presigned_url_expiry: int = 7  # Days
    zambia_csv_folder_path: str = "disbursements"
