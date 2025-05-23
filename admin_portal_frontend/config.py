from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ADMIN_PORTAL_BACKEND_URL: str = "http://admin-portal-backend-compose:8002" # Địa chỉ của admin_portal_backend_service trong Docker network
    APP_TITLE: str = "Admin Portal OCR"

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

