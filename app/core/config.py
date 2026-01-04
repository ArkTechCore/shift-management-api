# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shift Management API"
    API_V1_STR: str = "/api/v1"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    GROQ_MAX_TOKENS: int = 512
    GROQ_TEMPERATURE: float = 0.2

    # ENVIRONMENT
    ENV: str = "local"

    # SECURITY
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # DATABASE
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",   # <<< THIS FIXES YOUR ERROR
    )


settings = Settings()
