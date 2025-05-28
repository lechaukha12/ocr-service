from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Đặt tên biến môi trường khác để tránh xung đột nếu bạn dùng chung .env
    # Ví dụ: OCR_GEMINI_API_KEY
    # Giá trị mặc định "YOUR_OCR_GEMINI_API_KEY_HERE" chỉ là placeholder.
    # Bạn NÊN cung cấp giá trị thực qua biến môi trường.
    OCR_GEMINI_API_KEY: str = "AIzaSyBwzEI0ULM39xGZ3-kADT6vImYFOvx6Zdc" 

    class Config:
        env_file = ".env" # Pydantic-settings sẽ cố gắng đọc từ file .env
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()