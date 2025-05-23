# Trong ocr-service/api_gateway/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = "http://user-service-compose:8001"
    STORAGE_SERVICE_URL: str = "http://storage-service-compose:8003"
    ADMIN_PORTAL_BACKEND_SERVICE_URL: str = "http://admin-portal-backend-compose:8002"
    GENERIC_OCR_SERVICE_URL: str = "http://generic-ocr-service-compose:8004" # << THÊM DÒNG NÀY

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()