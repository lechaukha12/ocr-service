from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    USER_SERVICE_URL: str = "http://user-service-compose:8001"
    
    USER_SERVICE_JWT_SECRET_KEY: str = "Abcd1234"
    USER_SERVICE_ALGORITHM: str = "HS256"


    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
