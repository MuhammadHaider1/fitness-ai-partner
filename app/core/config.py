from pathlib import Path

from pydantic_settings import BaseSettings

Base_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):

    DATABASE_URL: str 
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str
    GROQ_API_KEY: str | None = None
    USDA_API_KEY : str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = Base_DIR / ".env"
        env_file_encoding = "utf-8"

settings = Settings() # type: ignore
    
