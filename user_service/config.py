from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "Abcd1234"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 30 minutes

    class Config:
        env_file = ".env" # Optional: Load from .env file if it exists

settings = Settings()