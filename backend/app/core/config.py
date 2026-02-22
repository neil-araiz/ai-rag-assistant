from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GOOGLE_API_KEY: str
    
    DATABASE_URL: str
    DIRECT_URL: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

Settings.model_rebuild()

@lru_cache()
def get_settings():
    return Settings()
