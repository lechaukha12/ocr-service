from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = "http://user-service-compose:8001" # Địa chỉ user_service trong Docker network

    # Sau này có thể thêm các cấu hình khác như secret key cho admin auth
    # ADMIN_SECRET_KEY: str = "your_admin_secret_key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
