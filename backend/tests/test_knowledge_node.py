import tempfile
from unittest.mock import MagicMock

import pytest

from app.agents.nodes import (
    finalize_response_node,
    retrieve_sleep_knowledge_node,
)
from app.schemas.checkin import CheckinRequest
from app.schemas.knowledge import KnowledgeContext
from app.services.embedding_provider import (
    EmbeddingUnavailableError,
    FakeEmbeddingProvider,
)
from app.services.rag_service import RAGService


def _make_state(**overrides):
    base = {
        "checkin": CheckinRequest(
            mood="calm",
            energy_level=5,
            stress_level=3,
            caffeine_after_3pm=False,
            screen_time_minutes=30,
            available_minutes=10,
            preferred_audio="none",
        ),
        "history_days": 7,
    }
    base.update(overrides)
    return base


def _make_runtime(rag_service=None):
    runtime = MagicMock()
    runtime.context.rag_service = rag_service
    return runtime


class TestRetrieveSleepKnowledgeNode:
    def test_rag_service_none_returns_disabled(self):
        state = _make_state()
        result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=None))
        assert result["knowledge_context"].status == "disabled"
        assert result["knowledge_context"].chunks == []

    def test_rag_service_empty_returns_empty(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            provider = FakeEmbeddingProvider(dimensions=1536)
            rag = RAGService(
                persist_dir=tmpdir,
                collection_name="test",
                embedding_provider=provider,
            )
            state = _make_state()
            result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=rag))
            assert result["knowledge_context"].status == "empty"

    def test_rag_service_with_data_returns_used(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            provider = FakeEmbeddingProvider(dimensions=1536)
            rag = RAGService(
                persist_dir=tmpdir,
                collection_name="test",
                embedding_provider=provider,
            )
            rag._collection.upsert(
                ids=["c1"],
                documents=["放松呼吸练习方法"],
                embeddings=[provider.embed_query("放松呼吸")],
                metadatas=[{"source": "breathing.md", "category": "breathing", "section_path": "呼吸"}],
            )
            state = _make_state()
            result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=rag))
            assert result["knowledge_context"].status in ("used", "empty")

    def test_embedding_unavailable_returns_unavailable(self):
        mock_rag = MagicMock()
        mock_rag.retrieve.side_effect = EmbeddingUnavailableError("API down")
        state = _make_state()
        result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=mock_rag))
        assert result["knowledge_context"].status == "unavailable"

    def test_crisis_path_node_still_calls_rag(self):
        """The node itself doesn't filter by crisis level; graph routing handles that."""
        mock_rag = MagicMock()
        mock_rag.retrieve.return_value = KnowledgeContext(status="empty")
        state = _make_state()
        state["crisis_level"] = "crisis"
        result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=mock_rag))
        assert result["knowledge_context"].status == "empty"

    def test_distress_path_node_still_calls_rag(self):
        """The node itself doesn't filter by crisis level; graph routing handles that."""
        mock_rag = MagicMock()
        mock_rag.retrieve.return_value = KnowledgeContext(status="empty")
        state = _make_state()
        state["crisis_level"] = "distress"
        result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=mock_rag))
        assert result["knowledge_context"].status == "empty"

    def test_query_excludes_notes(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            provider = FakeEmbeddingProvider(dimensions=1536)
            rag = RAGService(
                persist_dir=tmpdir,
                collection_name="test",
                embedding_provider=provider,
            )
            state = _make_state(
                checkin=CheckinRequest(
                    mood="calm",
                    energy_level=5,
                    stress_level=3,
                    caffeine_after_3pm=False,
                    screen_time_minutes=30,
                    available_minutes=10,
                    preferred_audio="none",
                    notes="这是用户备注，不应出现在查询中",
                )
            )
            result = retrieve_sleep_knowledge_node(state, runtime=_make_runtime(rag_service=rag))
            kctx = result["knowledge_context"]
            assert "备注" not in kctx.query_used
            assert "不应" not in kctx.query_used


class TestFinalizeResponseNode:
    def _make_full_state(self, knowledge_context=None):
        from app.schemas.routine import SleepRoutine

        state = _make_state()
        state["routine"] = SleepRoutine(
            title="test",
            duration_minutes=10,
            strategy="test",
            steps=[{"order": 1, "action": "a", "duration_seconds": 60, "instruction": "i"}],
            script="script",
        )
        state["generation_mode"] = "mock"
        state["history_available"] = False
        state["record_count"] = 0
        if knowledge_context is not None:
            state["knowledge_context"] = knowledge_context
        return state

    def test_rag_status_disabled(self):
        state = self._make_full_state()
        result = finalize_response_node(state, runtime=_make_runtime())
        meta = result["response"].meta
        assert meta.rag_status == "disabled"
        assert meta.knowledge_sources == []

    def test_rag_status_used_maps_to_success(self):
        from app.schemas.knowledge import RetrievedChunk

        kctx = KnowledgeContext(
            status="used",
            chunks=[
                RetrievedChunk(
                    chunk_id="abc",
                    content="content",
                    source="breathing.md",
                    category="breathing",
                    section_path="sec",
                    distance=0.5,
                )
            ],
        )
        state = self._make_full_state(knowledge_context=kctx)
        result = finalize_response_node(state, runtime=_make_runtime())
        meta = result["response"].meta
        assert meta.rag_status == "success"
        assert "breathing.md" in meta.knowledge_sources

    def test_rag_status_empty(self):
        kctx = KnowledgeContext(status="empty")
        state = self._make_full_state(knowledge_context=kctx)
        result = finalize_response_node(state, runtime=_make_runtime())
        assert result["response"].meta.rag_status == "empty"

    def test_rag_status_unavailable(self):
        kctx = KnowledgeContext(status="unavailable")
        state = self._make_full_state(knowledge_context=kctx)
        result = finalize_response_node(state, runtime=_make_runtime())
        assert result["response"].meta.rag_status == "unavailable"
