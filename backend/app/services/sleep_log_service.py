from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.sleep_log import SleepLogCreate
from app.repositories import sleep_log_repo


def create_sleep_log(db: Session, data: SleepLogCreate):
    existing = sleep_log_repo.get_log_by_date(db, data.log_date)
    if existing:
        raise HTTPException(status_code=409, detail=f"Log for {data.log_date} already exists")
    try:
        return sleep_log_repo.create_sleep_log(db, data)
    except Exception:
        db.rollback()
        raise


def get_recent_logs(db: Session, days: int = 7):
    return sleep_log_repo.get_recent_logs(db, days)
