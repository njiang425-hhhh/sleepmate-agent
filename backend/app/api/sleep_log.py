from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.sleep_log import SleepLogCreate, SleepLogResponse, SleepLogListResponse
from app.services import sleep_log_service

router = APIRouter()


@router.post("/sleep-log", response_model=SleepLogResponse, status_code=201)
async def create_sleep_log(request: SleepLogCreate, db: Session = Depends(get_db)):
    return sleep_log_service.create_sleep_log(db, request)


@router.get("/sleep-log/recent", response_model=SleepLogListResponse)
async def get_recent_sleep_logs(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    logs = sleep_log_service.get_recent_logs(db, days)
    return SleepLogListResponse(status="success", count=len(logs), logs=logs)
