import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Planning Agent"
    APP_VERSION: str = "0.1.0"
    
    # LLM Settings
    LLM_PROVIDER: str = "google" # openrouter, openai, google

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    
    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "z-ai/glm-4.5-air:free"

    # Google Gemini
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.5-flash"
    
    # Google Calendar
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    
    # User Constraints
    USER_WORKING_HOURS_START: str = "09:00"
    USER_WORKING_HOURS_END: str = "17:00"
    USER_LUNCH_START: str = "13:00"
    USER_LUNCH_END: str = "14:00"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
