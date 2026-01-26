# src/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "ContentAgent"
    VERSION: str = "1.0.0"
    
    OPENROUTER_API_KEY: str
    TAVILY_API_KEY: str
    SERPER_API_KEY: str
    
    # DATABASE 
    DATABASE_URL: str = "sqlite+aiosqlite:///./content_forge.db"

    class Config:
        
        env_file = ".env"
        extra = "ignore" 

@lru_cache()
def get_settings():
    return Settings()