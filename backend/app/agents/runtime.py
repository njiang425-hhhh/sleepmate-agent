from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.llm_provider import LLMProvider


@dataclass
class AgentRuntimeContext:
    db: Session
    provider: LLMProvider
