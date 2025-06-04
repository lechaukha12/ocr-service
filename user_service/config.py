from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SECRET_KEY: str = "Abcd1234"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_USERNAME_FOR_TESTING: str = "khalc"

    # Database Configuration
    POSTGRES_USER: str = "ocradmin"
    POSTGRES_PASSWORD: str = "ocrpassword"
    POSTGRES_DB: str = "ocrdb"
    DATABASE_URL: str = "postgresql://ocradmin:ocrpassword@postgres-compose:5432/ocrdb"

    class Config:
        env_file = ".env"

settings = Settings()
