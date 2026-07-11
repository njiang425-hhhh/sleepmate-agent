from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services import dashboard_service

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    return dashboard_service.get_dashboard_summary(db, days)
