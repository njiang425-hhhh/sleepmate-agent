from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.llm_provider import LLMProvider


@dataclass
class AgentRuntimeContext:
    db: Session
    provider: LLMProvider
    rag_service: object | None = field(default=None)
