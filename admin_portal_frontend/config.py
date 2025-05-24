from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    API_GATEWAY_URL: str = "http://api-gateway-compose:8000" # URL của API Gateway
    APP_TITLE: str = "Admin Portal OCR"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 

    SECRET_KEY: str = "Abcd1234" 
    ALGORITHM: str = "HS256"

    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    TEMPLATES_DIR_CONFIG: str = os.path.join(BASE_DIR, "templates")
    STATIC_DIR_CONFIG: str = os.path.join(BASE_DIR, "static")

    class Config:
        env_file = ".env" 
        extra = "ignore"

settings = Settings()

if not os.path.exists(settings.TEMPLATES_DIR_CONFIG):
    os.makedirs(settings.TEMPLATES_DIR_CONFIG)
if not os.path.exists(settings.STATIC_DIR_CONFIG):
    os.makedirs(settings.STATIC_DIR_CONFIG)

