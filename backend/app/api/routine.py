from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.routine import RoutineGenerateRequest, RoutineGenerateResponse
from app.services import routine_service

router = APIRouter()


@router.post("/routine/generate")
async def generate_routine(
    request: RoutineGenerateRequest,
    req: Request,
    db: Session = Depends(get_db),
) -> RoutineGenerateResponse:
    from app.main import get_rag_service

    rag_service = get_rag_service()
    return routine_service.generate_routine_via_graph(
        checkin=request.checkin,
        db=db,
        history_days=request.history_days,
        rag_service=rag_service,
    )
