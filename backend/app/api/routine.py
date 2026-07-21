import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.schemas.routine import RoutineGenerateRequest, RoutineGenerateResponse
from app.services import routine_service
from app.services.llm_provider import ProviderTimeoutError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/routine/generate")
@limiter.limit(settings.RATE_LIMIT_ROUTINE)
async def generate_routine(
    request: Request,
    body: RoutineGenerateRequest,
    db: Session = Depends(get_db),
) -> RoutineGenerateResponse:
    from app.main import get_rag_service

    rag_service = get_rag_service()
    try:
        return routine_service.generate_routine_via_graph(
            checkin=body.checkin,
            db=db,
            history_days=body.history_days,
            rag_service=rag_service,
        )
    except ProviderTimeoutError:
        raise HTTPException(status_code=503, detail="LLM 服务暂时不可用，请稍后重试")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in routine generation")
        raise HTTPException(status_code=500, detail="服务器内部错误")
