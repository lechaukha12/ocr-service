from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ADMIN_PORTAL_BACKEND_URL: str = "http://admin-portal-backend-compose:8002"
    APP_TITLE: str = "Admin Portal OCR"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Thời gian hết hạn token truy cập mặc định là 30 phút

    # Thêm các dòng này
    SECRET_KEY: str = "your_very_secret_key_for_frontend" # Thay bằng một chuỗi bí mật thực sự
    ALGORITHM: str = "HS256"

    # Sau này có thể thêm các cấu hình khác
    # STATIC_FILES_DIR: str = "static"
    # TEMPLATES_DIR: str = "templates"

    class Config:
        env_file = ".env" # Cho phép ghi đè bằng file .env
        extra = "ignore"

settings = Settings()

# Tạo đường dẫn tuyệt đối cho thư mục templates và static dựa trên vị trí file config.py
# Điều này quan trọng để Jinja2 và FastAPI tìm thấy các file này, đặc biệt khi chạy trong Docker.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR_CONFIG = os.path.join(BASE_DIR, "templates")
STATIC_DIR_CONFIG = os.path.join(BASE_DIR, "static")

# Đảm bảo các thư mục này tồn tại (mặc dù chúng ta đã tạo bằng lệnh mkdir)
if not os.path.exists(TEMPLATES_DIR_CONFIG):
    os.makedirs(TEMPLATES_DIR_CONFIG)
if not os.path.exists(STATIC_DIR_CONFIG):
    os.makedirs(STATIC_DIR_CONFIG)