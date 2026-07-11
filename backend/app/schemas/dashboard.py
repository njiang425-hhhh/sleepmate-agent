from typing import Optional
from pydantic import BaseModel


class ScoreBreakdownItem(BaseModel):
    score: int
    max_score: int
    label: str


class LatestScoreItem(BaseModel):
    date: str
    score: int
    level: str
    level_label: str
    breakdown: dict[str, ScoreBreakdownItem]


class DashboardAverages(BaseModel):
    sleep_latency_minutes: float
    awakenings: float
    sleep_quality: float
    stress_level: float
    screen_time_minutes: float
    score: float


class DashboardSummaryResponse(BaseModel):
    days: int
    record_count: int
    averages: Optional[DashboardAverages] = None
    latest_score: Optional[LatestScoreItem] = None
    advice: list[str]
