# app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "cambia-esto"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # <-- default

    class Config:
        env_file = ".env"

settings = Settings()
