from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ecommerce_data"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # ML Model settings
    SENTIMENT_MODEL_PATH: Optional[str] = None
    RECOMMENDATION_MODEL_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()