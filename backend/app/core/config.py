from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        extra = "ignore"

Settings.model_rebuild()

@lru_cache()
def get_settings():
    return Settings()
