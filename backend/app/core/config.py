from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "SleepMate Agent"
    API_PREFIX: str = "/api/v1"
    ENV: str = "development"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"


settings = Settings()
