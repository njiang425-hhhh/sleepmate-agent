import pytest

from app.services.embedding_provider import (
    EmbeddingConfigurationError,
    EmbeddingProvider,
    FakeEmbeddingProvider,
    OpenAIEmbeddingProvider,
)


class TestFakeEmbeddingProvider:
    def test_returns_correct_dimensions(self):
        p = FakeEmbeddingProvider(dimensions=128)
        v = p.embed_query("test")
        assert len(v) == 128

    def test_deterministic(self):
        p = FakeEmbeddingProvider()
        v1 = p.embed_query("hello")
        v2 = p.embed_query("hello")
        assert v1 == v2

    def test_different_inputs_different_vectors(self):
        p = FakeEmbeddingProvider()
        v1 = p.embed_query("hello")
        v2 = p.embed_query("world")
        assert v1 != v2

    def test_embed_texts(self):
        p = FakeEmbeddingProvider(dimensions=64)
        vectors = p.embed_texts(["a", "b", "c"])
        assert len(vectors) == 3
        assert all(len(v) == 64 for v in vectors)

    def test_embed_texts_empty(self):
        p = FakeEmbeddingProvider()
        assert p.embed_texts([]) == []

    def test_provider_name(self):
        p = FakeEmbeddingProvider()
        assert p.provider_name == "fake"

    def test_normalized(self):
        p = FakeEmbeddingProvider()
        v = p.embed_query("test")
        norm = sum(x * x for x in v) ** 0.5
        assert abs(norm - 1.0) < 1e-6


class TestOpenAIEmbeddingProvider:
    def test_missing_api_key_raises(self):
        with pytest.raises(EmbeddingConfigurationError):
            OpenAIEmbeddingProvider(api_key="")

    def test_provider_name(self):
        p = OpenAIEmbeddingProvider(api_key="test-key")
        assert p.provider_name == "openai"

    def test_dimensions(self):
        p = OpenAIEmbeddingProvider(api_key="test-key", dimensions=256)
        assert p.dimensions == 256
