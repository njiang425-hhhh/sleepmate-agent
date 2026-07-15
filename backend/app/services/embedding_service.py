from app.core.config import settings
from app.services.embedding_provider import (
    EmbeddingConfigurationError,
    EmbeddingProvider,
)


def create_embedding_provider() -> EmbeddingProvider:
    """根据 settings.EMBEDDING_PROVIDER 创建 provider.
    导入/配置失败 -> EmbeddingConfigurationError (启动终止).
    """
    if settings.EMBEDDING_PROVIDER == "fake":
        from app.services.embedding_provider import FakeEmbeddingProvider
        return FakeEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)
    if settings.EMBEDDING_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise EmbeddingConfigurationError(
                "OPENAI_API_KEY is required for OpenAI embedding. "
                "Set OPENAI_API_KEY or change EMBEDDING_PROVIDER to 'fake' for testing."
            )
        from app.services.embedding_provider import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
    raise EmbeddingConfigurationError(f"Unknown embedding provider: {settings.EMBEDDING_PROVIDER}")
