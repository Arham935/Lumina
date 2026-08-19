from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Enterprise_AI_Gateway"
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    ADMIN_API_KEY: str
    MODEL_CONFIG: dict = {
        "gpt-4o": {"cost": 25, "provider": "openai"},
        "gpt-4o-mini": {"cost": 1, "provider": "openai"},
        "llama3-70b-8192": {"cost": 0, "provider": "groq"}
    }
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings(): return Settings()
settings = get_settings()