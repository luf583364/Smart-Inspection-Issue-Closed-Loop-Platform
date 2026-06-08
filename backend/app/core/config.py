from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "机房智能巡检与问题闭环管理系统"
    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_TIMEZONE: str = "Asia/Shanghai"

    DATABASE_URL: str = "sqlite:///./inspection.db"

    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    UPLOAD_DIR: str = "./uploads"
    UPLOAD_BASE_URL: str = "/uploads"

    # Generated inspection reports (one self-contained HTML per record) live here.
    REPORTS_DIR: str = "./reports"

    PUBLIC_WEB_BASE_URL: str = "http://192.168.31.204:8001"
    FRONTEND_ROUTER_MODE: str = "hash"

    CORS_ORIGINS: List[str] = ["http://localhost:8001", "http://192.168.31.204:8001"]

    SEED_DEMO_DATA: bool = True
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "123456"
    BOOTSTRAP_ADMIN_NAME: str = "管理员"
    BOOTSTRAP_ADMIN_PHONE: str = "13800000000"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
