from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.sleep_log import SleepLog
from app.schemas.sleep_log import SleepLogCreate


def create_sleep_log(db: Session, data: SleepLogCreate) -> SleepLog:
    log = SleepLog(**data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_log_by_date(db: Session, log_date: date) -> SleepLog | None:
    return db.query(SleepLog).filter(SleepLog.log_date == log_date).first()


def get_recent_logs(db: Session, days: int = 7) -> list[SleepLog]:
    cutoff = date.today() - timedelta(days=days - 1)
    return (
        db.query(SleepLog)
        .filter(SleepLog.log_date >= cutoff)
        .order_by(SleepLog.log_date.desc())
        .all()
    )
