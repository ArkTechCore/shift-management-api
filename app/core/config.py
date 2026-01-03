# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shift Management API"
    API_V1_STR: str = "/api/v1"

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
