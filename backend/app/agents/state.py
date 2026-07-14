from typing import Literal, NotRequired, TypedDict

from app.schemas.checkin import CheckinRequest
from app.schemas.routine import RoutineGenerateResponse, SleepRoutine


class AgentInput(TypedDict):
    checkin: CheckinRequest
    history_days: int


class AgentOutput(TypedDict):
    response: RoutineGenerateResponse


class AgentState(TypedDict):
    checkin: CheckinRequest
    history_days: int

    crisis_level: NotRequired[Literal["none", "distress", "crisis"]]

    history_available: NotRequired[bool]
    record_count: NotRequired[int]
    avg_latency: NotRequired[float | None]
    avg_awakenings: NotRequired[float | None]
    avg_quality: NotRequired[float | None]
    avg_stress: NotRequired[float | None]
    avg_screen: NotRequired[float | None]

    routine: NotRequired[SleepRoutine | None]
    retry_count: NotRequired[int]
    generation_mode: NotRequired[
        Literal["mock", "real", "fallback", "rule_based"]
    ]
    safety_passed: NotRequired[bool]

    response: NotRequired[RoutineGenerateResponse | None]
