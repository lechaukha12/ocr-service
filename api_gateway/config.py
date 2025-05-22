# api_gateway/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = "http://user-service:8001" # Sử dụng tên service và port của user_service

    # ... các URL khác sau này
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()