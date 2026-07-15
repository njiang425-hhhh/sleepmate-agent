from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("RAG_MAX_DISTANCE", mode="before")
    @classmethod
    def parse_empty_distance(cls, v):
        if v == "" or v is None:
            return None
        return v

    APP_NAME: str = "SleepMate Agent"
    API_PREFIX: str = "/api/v1"
    ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./sleepmate.db"
    LLM_MODE: Literal["mock", "real"] = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30

    # RAG
    RAG_ENABLED: bool = False
    CHROMA_PERSIST_DIR: str = "chroma_db"
    CHROMA_COLLECTION_NAME: str = "sleepmate_knowledge"
    EMBEDDING_PROVIDER: Literal["openai", "fake"] = "fake"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    KNOWLEDGE_BASE_DIR: str = "data/knowledge_base"
    RAG_TOP_K: int = 3
    RAG_MAX_CONTEXT_TOKENS: int = 1500
    RAG_MAX_DISTANCE: float | None = None


settings = Settings()
