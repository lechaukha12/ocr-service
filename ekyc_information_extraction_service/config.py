from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Không còn GEMINI_API_KEY ở đây nữa
    # Bạn có thể thêm các cấu hình khác cho service nếu cần
    APP_NAME: str = "eKYC Information Extraction Service (Regex-Only)"

    class Config:
        env_file = ".env" 
        env_file_encoding = 'utf-8'
        extra = "ignore" 

settings = Settings()
