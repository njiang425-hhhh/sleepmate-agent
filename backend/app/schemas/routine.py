from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator, Field

from app.schemas.checkin import CheckinRequest


class RoutineStep(BaseModel):
    order: int = Field(ge=1, le=10)
    action: str
    duration_seconds: int = Field(gt=0, le=3600)
    instruction: str


class SleepRoutine(BaseModel):
    title: str
    duration_minutes: int = Field(ge=1, le=60)
    strategy: str
    steps: list[RoutineStep] = Field(min_length=1, max_length=10)
    script: str


class SafetyResource(BaseModel):
    name: str
    phone: str | None = None
    url: str | None = None


class RoutineMeta(BaseModel):
    history_available: bool
    history_record_count: int
    generation_mode: Literal["mock", "real", "fallback", "rule_based"]
    generated_at: datetime
    rag_status: Literal["success", "empty", "unavailable", "disabled", "error"] = "disabled"
    knowledge_sources: list[str] = Field(default_factory=list)


class RoutineSuccessResponse(BaseModel):
    type: Literal["success"] = "success"
    routine: SleepRoutine
    safety_notice: str
    meta: RoutineMeta


class SupportiveClarificationResponse(BaseModel):
    type: Literal["supportive_clarification"] = "supportive_clarification"
    message: str
    resources: list[SafetyResource]
    meta: RoutineMeta


class SafetyRedirectResponse(BaseModel):
    type: Literal["safety_redirect"] = "safety_redirect"
    message: str
    resources: list[SafetyResource]
    immediate_actions: list[str]
    meta: RoutineMeta


RoutineGenerateResponse = Annotated[
    Union[RoutineSuccessResponse, SupportiveClarificationResponse, SafetyRedirectResponse],
    Discriminator("type"),
]


class RoutineGenerateRequest(BaseModel):
    checkin: CheckinRequest
    history_days: int = Field(default=7, ge=1, le=30)
