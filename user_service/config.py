from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "Abcd1234"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_USERNAME_FOR_TESTING: str = "khalc"

    class Config:
        env_file = ".env"

settings = Settings()
