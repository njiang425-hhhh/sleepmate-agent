from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "SleepMate Agent"
    API_PREFIX: str = "/api/v1"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./sleepmate.db"
    LLM_MODE: Literal["mock", "real"] = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30


settings = Settings()
