import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "AI Fairy Tales API"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://ai-service:8001")
    AI_TEMPERATURE: float = 1.0
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")

settings = Settings()