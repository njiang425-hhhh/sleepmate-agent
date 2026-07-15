from abc import ABC, abstractmethod


class EmbeddingConfigurationError(Exception):
    """配置错误: API key 缺失、模型名无效. 启动时抛出, 终止进程."""


class EmbeddingUnavailableError(Exception):
    """运行时错误: API 超时、限流、网络故障. 允许优雅降级."""


class EmbeddingProvider(ABC):
    """Embedding 提供者抽象"""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量 embedding. 失败抛 EmbeddingUnavailableError."""
        ...

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """单条 query embedding. 失败抛 EmbeddingUnavailableError."""
        ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding 实现"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small", dimensions: int = 1536):
        if not api_key:
            raise EmbeddingConfigurationError("OPENAI_API_KEY is required for OpenAI embedding")
        self._model = model
        self._dimensions = dimensions
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)
        return self._client

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        all_embeddings: list[list[float]] = []
        batch_size = 2048
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                )
                all_embeddings.extend([item.embedding for item in response.data])
            except Exception as e:
                raise EmbeddingUnavailableError(f"OpenAI embedding failed: {e}") from e
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        client = self._get_client()
        try:
            response = client.embeddings.create(
                model=self._model,
                input=[query],
                dimensions=self._dimensions,
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingUnavailableError(f"OpenAI embedding failed: {e}") from e


class FakeEmbeddingProvider(EmbeddingProvider):
    """确定性伪向量, 仅用于测试. 不调用任何外部 API."""

    def __init__(self, dimensions: int = 1536):
        self._dimensions = dimensions

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _text_to_vector(self, text: str) -> list[float]:
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [b / 255.0 for b in h]
        while len(raw) < self._dimensions:
            raw.extend(raw[: min(len(raw), self._dimensions - len(raw))])
        norm = sum(v * v for v in raw) ** 0.5 or 1.0
        return [v / norm for v in raw[: self._dimensions]]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._text_to_vector(query)
