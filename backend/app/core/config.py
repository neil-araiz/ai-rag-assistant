from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GOOGLE_API_KEY: str
    
    USER: str
    PASSWORD: str
    HOST: str
    PORT: str
    DBNAME: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
