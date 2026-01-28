"""S3/MinIO configuration settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class S3Settings(BaseSettings):
    """S3-compatible storage configuration."""

    # Connection settings
    S3_ENDPOINT_URL: str = "http://minio:9000"  # Internal Docker network
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_REGION: str = "us-east-1"  # Required by boto3, MinIO ignores it

    # Bucket configuration
    S3_BUCKET_NAME: str = "ip2a-documents"
    S3_PRESIGNED_URL_EXPIRY: int = 3600  # 1 hour for presigned URLs

    # File upload settings
    MAX_FILE_SIZE_MB: int = 50  # Maximum file size in MB
    ALLOWED_EXTENSIONS: set = {
        "pdf", "doc", "docx", "xls", "xlsx",
        "jpg", "jpeg", "png", "gif",
        "txt", "csv", "json"
    }

    class Config:
        env_file = ".env.compose"
        extra = "ignore"


@lru_cache()
def get_s3_settings() -> S3Settings:
    """Get cached S3 settings."""
    return S3Settings()
