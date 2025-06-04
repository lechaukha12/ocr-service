from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    UPLOAD_DIR: str = "uploads" # Thư mục lưu trữ file upload, tương đối với vị trí chạy main.py
    BASE_URL: str = "http://localhost:8003"  # Thêm BASE_URL để build link file trả về
    # MAX_FILE_SIZE_MB: int = 5 # Ví dụ: giới hạn kích thước file tối đa là 5MB
    # ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png"] # Ví dụ: chỉ cho phép các đuôi file này

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Đảm bảo thư mục UPLOAD_DIR tồn tại khi module này được import
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)

