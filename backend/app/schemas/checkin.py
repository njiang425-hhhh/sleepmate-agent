from typing import Literal, Optional

from pydantic import BaseModel, Field


MoodType = Literal["calm", "relaxed", "anxious", "excited", "tired", "stressed"]
AudioType = Literal["none", "rain", "ocean", "white_noise", "forest", "piano"]
AvailableMinutesType = Literal[5, 10, 15, 20]


class CheckinRequest(BaseModel):
    mood: MoodType
    energy_level: int = Field(ge=1, le=10)
    stress_level: int = Field(ge=1, le=10)
    caffeine_after_3pm: bool
    screen_time_minutes: int = Field(ge=0)
    available_minutes: AvailableMinutesType
    preferred_audio: AudioType
    notes: Optional[str] = None


class AnalysisResult(BaseModel):
    sleep_risk_level: str
    suggestions: list[str]
    recommended_activity: str
    recommended_duration_minutes: int


class CheckinResponse(BaseModel):
    status: str
    checkin: CheckinRequest
    analysis: AnalysisResult
