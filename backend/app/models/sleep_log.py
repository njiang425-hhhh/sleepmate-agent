from datetime import date, datetime, time
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, Time, CheckConstraint, func
from app.core.database import Base


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_date = Column(Date, nullable=False, unique=True, index=True)
    bedtime = Column(Time, nullable=False)
    wake_time = Column(Time, nullable=False)
    sleep_latency_minutes = Column(Integer, nullable=False, default=0)
    awakenings = Column(Integer, nullable=False, default=0)
    sleep_quality = Column(Integer, nullable=False)
    mood_before_sleep = Column(String(20), nullable=False)
    stress_level = Column(Integer, nullable=False)
    caffeine_after_3pm = Column(Boolean, nullable=False, default=False)
    screen_time_minutes = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("sleep_quality BETWEEN 1 AND 5", name="ck_sleep_quality"),
        CheckConstraint("stress_level BETWEEN 1 AND 10", name="ck_stress_level"),
        CheckConstraint("sleep_latency_minutes >= 0", name="ck_sleep_latency"),
        CheckConstraint("awakenings >= 0", name="ck_awakenings"),
    )
