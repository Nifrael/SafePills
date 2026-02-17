import os
from functools import lru_cache

class Settings:
    PROJECT_NAME: str = "SafePills API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    ENV: str = os.getenv("ENV", "development")
    IS_PRODUCTION: bool = ENV == "production"
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH: str = os.path.join(BASE_DIR, "data", "safepills.db")
    
    API_KEY: str = os.getenv("API_KEY")
    
    ALLOWED_ORIGINS: list = [
        origin.strip() 
        for origin in os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:4321,http://127.0.0.1:4321,https://pharma-tools-ten.vercel.app"
        ).split(",")
    ]
    if "https://pharma-tools-ten.vercel.app" not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append("https://pharma-tools-ten.vercel.app")

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
