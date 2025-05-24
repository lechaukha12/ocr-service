from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "AIzaSyBwzEI0ULM39xGZ3-kADT6vImYFOvx6Zdc" 

    class Config:
        env_file = ".env" # Tên file .env mặc định
        env_file_encoding = 'utf-8'
        extra = "ignore" # Bỏ qua các biến môi trường không được định nghĩa trong Settings

settings = Settings()

