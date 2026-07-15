import tempfile
from pathlib import Path

import pytest

from app.services.embedding_provider import FakeEmbeddingProvider
from scripts.ingest_knowledge import (
    generate_chunk_id,
    ingest_documents,
    parse_frontmatter,
    split_document,
)


class TestParseFrontmatter:
    def test_with_frontmatter(self):
        text = "---\ncurated_by: Team\nversion: 1.0\n---\n\n# Title\nContent here"
        meta, body = parse_frontmatter(text)
        assert meta["curated_by"] == "Team"
        assert meta["version"] == "1.0"
        assert "# Title" in body

    def test_without_frontmatter(self):
        text = "# Title\nContent here"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text


class TestSplitDocument:
    def test_basic_split(self):
        doc = "# Title\n\n## Section A\n\n" + "A" * 200 + "\n\n## Section B\n\n" + "B" * 200
        chunks = split_document("test.md", doc, {})
        assert len(chunks) >= 2

    def test_chunk_metadata(self):
        doc = "# Title\n\n## 睡眠环境\n\n保持黑暗。"
        chunks = split_document("sleep_hygiene.md", doc, {})
        assert len(chunks) >= 1
        assert chunks[0]["metadata"]["source"] == "sleep_hygiene.md"
        assert chunks[0]["metadata"]["category"] == "sleep_hygiene"

    def test_short_chunks_merged(self):
        doc = "# Title\n\n## A\n\n" + "Short content here. " * 10 + "\n\n## B\n\n" + "Another short. " * 10
        chunks = split_document("test.md", doc, {})
        for c in chunks:
            assert len(c["content"]) >= 50 or len(chunks) == 1


class TestGenerateChunkId:
    def test_deterministic(self):
        id1 = generate_chunk_id("a.md", "sec", "content")
        id2 = generate_chunk_id("a.md", "sec", "content")
        assert id1 == id2

    def test_different_content(self):
        id1 = generate_chunk_id("a.md", "sec", "content1")
        id2 = generate_chunk_id("a.md", "sec", "content2")
        assert id1 != id2

    def test_full_sha256_length(self):
        chunk_id = generate_chunk_id("a.md", "sec", "content")
        assert len(chunk_id) == 64


class TestIngestIdempotency:
    def test_idempotent_import(self):
        provider = FakeEmbeddingProvider(dimensions=1536)
        kb_dir = str(Path(__file__).resolve().parent.parent / "data" / "knowledge_base")

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            r1 = ingest_documents(kb_dir, tmpdir, "test_col", provider)
            r2 = ingest_documents(kb_dir, tmpdir, "test_col", provider)
            assert r1.total_chunks == r2.total_chunks
            assert r2.deleted_stale == 0

    def test_stale_chunk_deletion(self):
        provider = FakeEmbeddingProvider(dimensions=1536)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            import chromadb

            client = chromadb.PersistentClient(path=tmpdir)
            col = client.get_or_create_collection(
                name="test_col",
                metadata={"hnsw:space": "cosine", "dataset_id": "default",
                           "embedding_provider": "fake", "embedding_model": "",
                           "dimensions": "1536", "distance_metric": "cosine", "schema_version": "1"},
            )
            col.upsert(
                ids=["stale_id"],
                documents=["stale content"],
                embeddings=[provider.embed_query("stale")],
                metadatas=[{"dataset_id": "default"}],
            )
            assert col.count() == 1

            kb_dir = str(Path(__file__).resolve().parent.parent / "data" / "knowledge_base")
            result = ingest_documents(kb_dir, tmpdir, "test_col", provider)
            assert result.deleted_stale == 1

    def test_import_preserves_existing_data(self):
        provider = FakeEmbeddingProvider(dimensions=1536)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            kb_dir = str(Path(__file__).resolve().parent.parent / "data" / "knowledge_base")
            r1 = ingest_documents(kb_dir, tmpdir, "test_col", provider)
            assert r1.total_chunks > 0

            import chromadb
            client = chromadb.PersistentClient(path=tmpdir)
            col = client.get_collection("test_col")
            count_before = col.count()
            assert count_before == r1.total_chunks
