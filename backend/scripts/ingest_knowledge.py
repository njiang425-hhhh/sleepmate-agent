"""幂等知识库导入脚本.

用法:
    cd backend
    python -m scripts.ingest_knowledge

流程:
    1. 解析所有 .md 文件的 frontmatter 和内容
    2. 按标题切分为 chunks, 生成稳定 chunk_id (SHA256)
    3. 分批 embedding + 维度校验
    4. 全部成功后 upsert + 删除同一 dataset_id 下的陈旧 chunk
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

# 确保 backend 在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.services.embedding_provider import EmbeddingConfigurationError, EmbeddingProvider
from app.services.embedding_service import create_embedding_provider


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML frontmatter, 返回 (metadata, body)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    meta = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, text[m.end():]


def split_document(source: str, body: str, frontmatter: dict) -> list[dict]:
    """按标题切分文档, 返回 chunk 列表."""
    sections: list[tuple[str, str, str]] = []
    headings = list(HEADING_RE.finditer(body))

    if not headings:
        sections.append(("(全文)", "", body.strip()))
        return _build_chunks(source, sections, frontmatter)

    first_content = body[: headings[0].start()].strip()
    if first_content:
        sections.append(("(引言)", "", first_content))

    for i, h in enumerate(headings):
        level = len(h.group(1))
        title = h.group(2).strip()
        start = h.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        content = body[start:end].strip()
        if not content:
            continue
        section_path = title
        sections.append((section_path, f"{'#' * level} {title}", content))

    return _build_chunks(source, sections, frontmatter)


def _build_chunks(source: str, sections: list[tuple], frontmatter: dict) -> list[dict]:
    """将 sections 转换为 chunks, 执行合并和切分."""
    category = source.replace(".md", "")
    chunks: list[dict] = []
    pending_content = ""

    for section_path, heading, content in sections:
        full_text = f"{heading}\n\n{content}".strip() if heading else content
        if not full_text:
            continue

        if len(full_text) < 80:
            pending_content = (pending_content + "\n\n" + full_text).strip() if pending_content else full_text
        else:
            if pending_content:
                chunks.append(_make_chunk(source, category, section_path, pending_content, frontmatter))
                pending_content = ""
            if len(full_text) > 1000:
                sub_chunks = _split_long_section(source, category, section_path, full_text, frontmatter)
                chunks.extend(sub_chunks)
            else:
                pending_content = full_text

    if pending_content:
        chunks.append(_make_chunk(source, category, sections[-1][0] if sections else "(全文)", pending_content, frontmatter))

    return chunks


def _split_long_section(source: str, category: str, section_path: str, text: str, frontmatter: dict) -> list[dict]:
    """对超长 section 按段落切分."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    result: list[dict] = []
    buffer = ""
    for p in paragraphs:
        if len(buffer) + len(p) > 800 and buffer:
            result.append(_make_chunk(source, category, section_path, buffer, frontmatter))
            buffer = p
        else:
            buffer = (buffer + "\n\n" + p).strip() if buffer else p
    if buffer:
        result.append(_make_chunk(source, category, section_path, buffer, frontmatter))
    return result


def generate_chunk_id(source: str, section_path: str, content: str) -> str:
    """稳定 chunk_id: SHA256(source::section_path::stripped_content)."""
    raw = f"{source}::{section_path}::{content.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _make_chunk(source: str, category: str, section_path: str, content: str, frontmatter: dict) -> dict:
    chunk_id = generate_chunk_id(source, section_path, content)
    metadata = {
        "source": source,
        "category": category,
        "section_path": section_path,
        "chunk_id": chunk_id,
        "source_org": frontmatter.get("curated_by", "SleepMate Research Team"),
        "version": frontmatter.get("version", "1.0.0"),
        "reviewed_at": frontmatter.get("reviewed_at", ""),
        "language": frontmatter.get("language", "zh-CN"),
        "license": frontmatter.get("license", "CC-BY-4.0"),
    }
    return {"id": chunk_id, "content": content, "metadata": metadata}


class IngestResult:
    def __init__(self, total_chunks: int, sources: list[str], deleted_stale: int):
        self.total_chunks = total_chunks
        self.sources = sources
        self.deleted_stale = deleted_stale

    def __repr__(self):
        return f"IngestResult(total_chunks={self.total_chunks}, sources={self.sources}, deleted_stale={self.deleted_stale})"


def ingest_documents(
    knowledge_dir: str,
    persist_dir: str,
    collection_name: str,
    embedding_provider: EmbeddingProvider,
    dataset_id: str = "default",
    max_distance: float | None = None,
) -> IngestResult:
    """幂等导入: 解析 -> embedding -> upsert -> 清理陈旧."""
    import chromadb

    kb_path = Path(knowledge_dir)
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {knowledge_dir}")

    # Phase 1: 解析 + 切分
    all_chunks: list[dict] = []
    sources: list[str] = []
    for md_file in sorted(kb_path.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        chunks = split_document(md_file.name, body, frontmatter)
        all_chunks.extend(chunks)
        sources.append(md_file.name)
        print(f"  {md_file.name}: {len(chunks)} chunks")

    if not all_chunks:
        print("No chunks found.")
        return IngestResult(0, sources, 0)

    print(f"\nTotal chunks to embed: {len(all_chunks)}")

    # Phase 2: embedding + 维度校验
    contents = [c["content"] for c in all_chunks]
    embeddings = embedding_provider.embed_texts(contents)

    if len(embeddings) != len(all_chunks):
        raise RuntimeError(f"Embedding count mismatch: {len(embeddings)} != {len(all_chunks)}")

    for i, emb in enumerate(embeddings):
        if len(emb) != embedding_provider.dimensions:
            raise RuntimeError(
                f"Dimension mismatch at chunk {i}: "
                f"got {len(emb)}, expected {embedding_provider.dimensions}"
            )

    print(f"All {len(embeddings)} embeddings validated (dim={embedding_provider.dimensions})")

    # Phase 3: upsert + 清理陈旧
    client = chromadb.PersistentClient(path=persist_dir)
    expected_metadata = {
        "embedding_provider": embedding_provider.provider_name,
        "embedding_model": settings.EMBEDDING_MODEL,
        "dimensions": str(embedding_provider.dimensions),
        "distance_metric": "cosine",
        "schema_version": "1",
        "dataset_id": dataset_id,
    }
    col = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", **expected_metadata},
    )

    # 获取当前 dataset_id 下的所有已有 ID
    existing = col.get(where={"dataset_id": dataset_id} if dataset_id else None)
    existing_ids = set(existing["ids"]) if existing["ids"] else set()

    # Upsert 新 chunks
    new_ids = [c["id"] for c in all_chunks]
    new_contents = [c["content"] for c in all_chunks]
    new_metadatas = [c["metadata"] for c in all_chunks]

    batch_size = 100
    for i in range(0, len(new_ids), batch_size):
        col.upsert(
            ids=new_ids[i : i + batch_size],
            documents=new_contents[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            metadatas=new_metadatas[i : i + batch_size],
        )

    # 清理陈旧 chunk
    new_ids_set = set(new_ids)
    stale_ids = list(existing_ids - new_ids_set)
    if stale_ids:
        col.delete(ids=stale_ids)

    result = IngestResult(
        total_chunks=len(all_chunks),
        sources=sources,
        deleted_stale=len(stale_ids),
    )
    print(f"\nIngest complete: {result}")
    return result


def main():
    print("=== SleepMate Knowledge Base Ingest ===\n")

    try:
        provider = create_embedding_provider()
    except EmbeddingConfigurationError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    kb_dir = str(Path(__file__).resolve().parent.parent / settings.KNOWLEDGE_BASE_DIR)
    persist_dir = str(Path(__file__).resolve().parent.parent / settings.CHROMA_PERSIST_DIR)

    print(f"Knowledge base: {kb_dir}")
    print(f"Chroma persist: {persist_dir}")
    print(f"Embedding provider: {provider.provider_name} (dim={provider.dimensions})\n")

    t0 = time.time()
    result = ingest_documents(
        knowledge_dir=kb_dir,
        persist_dir=persist_dir,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_provider=provider,
        dataset_id="default",
    )
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
