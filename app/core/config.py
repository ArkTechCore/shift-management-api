from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Shift Management API"
    ENV: str = "local"

    # Use "*" for now while testing. Later we’ll lock it down.
    CORS_ORIGINS: str = "*"

    # Render will provide this as an env var later
    DATABASE_URL: str = ""

    JWT_SECRET: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
