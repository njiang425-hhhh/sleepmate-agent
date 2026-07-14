from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.routine import RoutineGenerateRequest, RoutineGenerateResponse
from app.services import routine_service

router = APIRouter()


@router.post("/routine/generate")
async def generate_routine(
    request: RoutineGenerateRequest,
    db: Session = Depends(get_db),
) -> RoutineGenerateResponse:
    return routine_service.generate_routine_via_graph(
        checkin=request.checkin,
        db=db,
        history_days=request.history_days,
    )
