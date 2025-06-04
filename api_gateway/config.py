from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = "http://user-service-compose:8001"
    STORAGE_SERVICE_URL: str = "http://storage-service-compose:8003"
    ADMIN_PORTAL_BACKEND_SERVICE_URL: str = "http://admin-portal-backend-compose:8002"
    GENERIC_OCR_SERVICE_URL: str = "http://generic-ocr-service-compose:8004"
    EKYC_INFO_EXTRACTION_SERVICE_URL: str = "http://ekyc-info-extraction-service-compose:8005"
    SECRET_KEY: str = "Abcd1234"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

