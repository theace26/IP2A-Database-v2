from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: Optional[str] = None
    IP2A_ENV: str = "dev"  # dev | test | prod

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
