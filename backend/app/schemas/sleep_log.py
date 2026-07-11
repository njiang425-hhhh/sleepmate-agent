from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, Field


class SleepLogCreate(BaseModel):
    log_date: date
    bedtime: time
    wake_time: time
    sleep_latency_minutes: int = Field(ge=0, le=120)
    awakenings: int = Field(ge=0, le=20)
    sleep_quality: int = Field(ge=1, le=5)
    mood_before_sleep: str = Field(min_length=1, max_length=20)
    stress_level: int = Field(ge=1, le=10)
    caffeine_after_3pm: bool = False
    screen_time_minutes: int = Field(ge=0)
    notes: Optional[str] = None


class SleepLogResponse(BaseModel):
    id: int
    log_date: date
    bedtime: time
    wake_time: time
    sleep_latency_minutes: int
    awakenings: int
    sleep_quality: int
    mood_before_sleep: str
    stress_level: int
    caffeine_after_3pm: bool
    screen_time_minutes: int
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SleepLogListResponse(BaseModel):
    status: str
    count: int
    logs: list[SleepLogResponse]
