import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "SafePills API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    ENV: str = "development"
    
    API_KEY: str = ""
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "https://safe-pills-ten.vercel.app"
    ]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENV == "production"

    @property
    def BASE_DIR(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @property
    def DB_PATH(self) -> str:
        return os.path.join(self.BASE_DIR, "data", "safepills.db")

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
