import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "College Validator AI API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Storage
    DATA_DIR: str = "data"
    CATALOGS_DIR: str = "data/catalogs"
    REPORTS_DIR: str = "data/reports"

    # Jobs
    JOB_TTL_SECONDS: int = 7200  # 2 hours

    # Ingestion
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_URL_DOWNLOAD_SIZE_MB: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)


settings = Settings()

# Ensure data directories exist
os.makedirs(settings.CATALOGS_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
