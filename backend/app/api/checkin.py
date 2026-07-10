from fastapi import APIRouter

from app.schemas.checkin import CheckinRequest
from app.services.checkin_service import analyze_checkin

router = APIRouter()


@router.post("/checkin")
async def create_checkin(request: CheckinRequest):
    analysis = analyze_checkin(request)
    return {
        "status": "success",
        "checkin": request.model_dump(),
        "analysis": analysis.model_dump(),
    }
