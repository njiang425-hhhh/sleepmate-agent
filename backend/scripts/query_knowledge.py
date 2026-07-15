"""独立知识库查询脚本 (调试用).

用法:
    cd backend
    python -m scripts.query_knowledge "高压力放松呼吸"

注意: 使用真实 OpenAI API 时需要设置 OPENAI_API_KEY.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.services.embedding_service import create_embedding_provider
from app.services.rag_service import RAGService


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.query_knowledge '<query>'")
        sys.exit(1)

    query = sys.argv[1]
    print(f"Query: {query}\n")

    try:
        provider = create_embedding_provider()
    except Exception as e:
        print(f"Embedding provider error: {e}")
        sys.exit(1)

    persist_dir = str(Path(__file__).resolve().parent.parent / settings.CHROMA_PERSIST_DIR)
    rag = RAGService(
        persist_dir=persist_dir,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        embedding_provider=provider,
        top_k=settings.RAG_TOP_K,
        max_distance=settings.RAG_MAX_DISTANCE,
        embedding_model=settings.EMBEDDING_MODEL,
    )

    print(f"Available: {rag.is_available()}")
    if not rag.is_available():
        print("No data in collection. Run ingest first.")
        sys.exit(0)

    from app.schemas.checkin import CheckinRequest
    fake_checkin = CheckinRequest(
        mood="stressed",
        energy_level=5,
        stress_level=8,
        caffeine_after_3pm=False,
        screen_time_minutes=60,
        available_minutes=15,
        preferred_audio="rain",
    )
    ctx = rag.retrieve(fake_checkin)
    print(f"Status: {ctx.status}")
    print(f"Chunks in DB: {ctx.total_chunks_in_db}")
    print(f"Query used: {ctx.query_used}")
    print(f"Results: {len(ctx.chunks)}\n")

    for i, chunk in enumerate(ctx.chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Source: {chunk.source} > {chunk.section_path}")
        print(f"  Distance: {chunk.distance:.4f}")
        print(f"  Content: {chunk.content[:200]}...")
        print()


if __name__ == "__main__":
    main()
