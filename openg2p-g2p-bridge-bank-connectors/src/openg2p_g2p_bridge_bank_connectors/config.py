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
    bank_simulator_code: str = "ACCESS_BANK"
    disbursement_batch_control_callback_url: str = "https://your-app.com/webhook"

    # Access Bank Auth API configuration
    access_bank_token_url: str = "https://access-bank.dev.openg2p.org/api/access-bank/token"
    access_bank_client_id: str = "your_access_bank_client_id"
    access_bank_wallet_payment_batch_url: str = (
        "https://access-bank.dev.openg2p.org/api/access-bank/mobile_wallet_payment"
    )
    access_bank_client_secret: str = "your_access_bank_client_secret"
    access_bank_grant_type: str = "client_credentials"
    access_bank_company_id: str = "COMP-001"

    # Minio configuration for Zambia CSV Connector
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "zambia-csv-files"
    minio_secure: bool = False
    zambia_csv_folder_path: str = "disbursements"
