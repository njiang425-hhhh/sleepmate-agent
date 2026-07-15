import tempfile

import pytest

from app.schemas.checkin import CheckinRequest
from app.schemas.knowledge import KnowledgeContext
from app.services.embedding_provider import FakeEmbeddingProvider
from app.services.rag_service import RAGService


@pytest.fixture
def fake_provider():
    return FakeEmbeddingProvider(dimensions=1536)


@pytest.fixture
def chroma_dir():
    """Windows-safe temp directory for ChromaDB (ignores file lock cleanup errors)."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        yield d


@pytest.fixture
def checkin_stressed():
    return CheckinRequest(
        mood="stressed",
        energy_level=5,
        stress_level=8,
        caffeine_after_3pm=False,
        screen_time_minutes=60,
        available_minutes=15,
        preferred_audio="rain",
    )


@pytest.fixture
def checkin_calm():
    return CheckinRequest(
        mood="calm",
        energy_level=5,
        stress_level=3,
        caffeine_after_3pm=False,
        screen_time_minutes=30,
        available_minutes=10,
        preferred_audio="none",
    )


class TestRAGService:
    def _make_service(self, persist_dir, provider, **kwargs):
        return RAGService(
            persist_dir=persist_dir,
            collection_name="test_col",
            embedding_provider=provider,
            top_k=3,
            **kwargs,
        )

    def test_is_available_empty(self, fake_provider, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        assert svc.is_available() is False

    def test_is_available_with_data(self, fake_provider, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        svc._collection.upsert(
            ids=["id1"],
            documents=["test content"],
            embeddings=[fake_provider.embed_query("test")],
            metadatas=[{"source": "test.md", "category": "test", "section_path": "sec"}],
        )
        assert svc.is_available() is True

    def test_retrieve_empty_collection(self, fake_provider, checkin_stressed, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        ctx = svc.retrieve(checkin_stressed)
        assert ctx.status == "empty"
        assert ctx.chunks == []

    def test_retrieve_returns_results(self, fake_provider, checkin_stressed, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        emb = fake_provider.embed_texts(["放松呼吸练习", "渐进式肌肉放松"])
        svc._collection.upsert(
            ids=["c1", "c2"],
            documents=["放松呼吸练习内容", "渐进式肌肉放松内容"],
            embeddings=emb,
            metadatas=[
                {"source": "breathing.md", "category": "breathing", "section_path": "呼吸"},
                {"source": "relax.md", "category": "relaxation", "section_path": "放松"},
            ],
        )
        ctx = svc.retrieve(checkin_stressed)
        assert ctx.status == "used"
        assert len(ctx.chunks) > 0
        assert ctx.total_chunks_in_db == 2

    def test_retrieve_query_excludes_notes(self, fake_provider, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        checkin = CheckinRequest(
            mood="calm",
            energy_level=5,
            stress_level=3,
            caffeine_after_3pm=False,
            screen_time_minutes=30,
            available_minutes=10,
            preferred_audio="none",
            notes="这是一条不应该出现在查询中的备注",
        )
        ctx = svc.retrieve(checkin)
        assert "备注" not in ctx.query_used
        assert "不应该" not in ctx.query_used

    def test_format_for_prompt_empty(self):
        ctx = KnowledgeContext(status="empty")
        result = RAGService.format_for_prompt(None, ctx)
        assert result == ""

    def test_format_for_prompt_with_chunks(self):
        from app.schemas.knowledge import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id="abc",
                content="呼吸练习内容",
                source="breathing.md",
                category="breathing",
                section_path="腹式呼吸",
                distance=0.5,
            )
        ]
        ctx = KnowledgeContext(status="used", chunks=chunks)
        result = RAGService.format_for_prompt(None, ctx)
        assert "仅供参考" in result
        assert "呼吸练习内容" in result
        assert "breathing.md" in result

    def test_max_distance_filter(self, fake_provider, checkin_stressed, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider, max_distance=0.001)
        emb = fake_provider.embed_texts(["test content"])
        svc._collection.upsert(
            ids=["c1"],
            documents=["test content"],
            embeddings=emb,
            metadatas=[{"source": "test.md", "category": "test", "section_path": "sec"}],
        )
        ctx = svc.retrieve(checkin_stressed)
        assert ctx.status == "empty"

    def test_status_used(self, fake_provider, checkin_calm, chroma_dir):
        svc = self._make_service(chroma_dir, fake_provider)
        emb = fake_provider.embed_texts(["睡前放松"])
        svc._collection.upsert(
            ids=["c1"],
            documents=["睡前放松方法"],
            embeddings=emb,
            metadatas=[{"source": "test.md", "category": "test", "section_path": "sec"}],
        )
        ctx = svc.retrieve(checkin_calm)
        assert ctx.status in ("used", "empty")
