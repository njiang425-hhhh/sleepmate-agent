from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """单个检索到的知识 chunk"""

    chunk_id: str
    content: str
    source: str
    category: str
    section_path: str
    distance: float


class KnowledgeContext(BaseModel):
    """结构化的检索上下文"""

    status: str = Field(
        default="disabled",
        description="used | empty | unavailable | disabled",
    )
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    query_used: str = ""
    total_chunks_in_db: int = 0
