import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SafePills API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    ENV: str = "development"
    
    API_KEY: str = ""
    
    ALLOWED_ORIGINS: str = "http://localhost:4321,http://127.0.0.1:4321,https://safe-pills-ten.vercel.app"

    @property
    def allowed_origins_list(self) -> list:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

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
