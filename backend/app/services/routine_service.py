import re
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.orm import Session

from app.repositories import sleep_log_repo
from app.schemas.checkin import CheckinRequest
from app.schemas.routine import (
    RoutineMeta,
    RoutineStep,
    RoutineSuccessResponse,
    SafetyRedirectResponse,
    SleepRoutine,
    SupportiveClarificationResponse,
)
from app.services.llm_provider import (
    LLMProvider,
    ProviderError,
    ProviderRefusedError,
    ProviderTimeoutError,
    RoutineGenerationContext,
)
from app.services.llm_service import SYSTEM_PROMPT, build_user_prompt, get_provider
from app.services.safety_resources import DEFAULT_RESOURCES

SAFETY_NOTICE = "本计划仅供参考，不替代专业医疗建议。如有持续睡眠问题，请咨询医生。"

MEDICAL_TERMS = [
    "诊断", "疾病", "治疗", "处方", "药物", "药方",
    "失眠症", "抑郁症", "焦虑症", "睡眠障碍",
]

DRUG_TERMS = [
    "褪黑素", "安眠药", "阿普唑仑", "佐匹克隆", "地西泮",
    "助眠药", "镇静剂", "抗组胺", "苯二氮卓",
]

CRISIS_KEYWORDS = [
    "想死", "自杀", "自伤", "活不下去", "不想活", "结束生命",
    "割腕", "跳楼", "吃药自杀", "遗书", "想消失",
]

DISTRESS_KEYWORDS = [
    "太痛苦了", "受不了了", "很难受", "好累", "撑不住",
    "很绝望", "好绝望", "崩溃", "情绪崩溃", "不想面对",
    "没有意义", "活着没意思",
]

NEGATION_PATTERNS = [
    r"不.{0,2}(?:想死|自杀|自伤|活不下去|不想活|结束生命)",
    r"没.{0,2}(?:想死|自杀|自伤)",
]

QUOTATION_PATTERNS = [
    r"(?:电影|小说|书|剧|故事|文章|新闻|台词).{0,10}(?:想死|自杀|自伤|活不下去)",
    r"(?:说|讲|写|提到).{0,5}(?:想死|自杀|自伤)",
    r"(?:别人|他人|角色).{0,5}(?:想死|自杀|自伤)",
]


class CrisisLevel(str, Enum):
    NONE = "none"
    DISTRESS = "distress"
    CRISIS = "crisis"


def detect_crisis_level(notes: str | None) -> CrisisLevel:
    if not notes:
        return CrisisLevel.NONE

    text = notes.strip()

    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, text):
            return CrisisLevel.NONE

    for pattern in QUOTATION_PATTERNS:
        if re.search(pattern, text):
            return CrisisLevel.NONE

    for kw in CRISIS_KEYWORDS:
        if kw in text:
            return CrisisLevel.CRISIS

    for kw in DISTRESS_KEYWORDS:
        if kw in text:
            return CrisisLevel.DISTRESS

    return CrisisLevel.NONE


FALLBACK_ROUTINE = SleepRoutine(
    title="呼吸引导放松",
    duration_minutes=5,
    strategy="基础呼吸引导，帮助身心放松",
    steps=[
        RoutineStep(order=1, action="准备就位", duration_seconds=30,
                    instruction="找一个舒适的姿势坐好或躺下，轻轻闭上眼睛，将双手自然放在身体两侧。"),
        RoutineStep(order=2, action="深呼吸练习", duration_seconds=180,
                    instruction='用鼻子缓慢吸气4秒，感受腹部隆起；屏息4秒；用嘴缓慢呼气6秒。重复6次，每次呼气时默念"放松"。'),
        RoutineStep(order=3, action="放松收尾", duration_seconds=90,
                    instruction="保持自然呼吸，想象温暖的光芒从头顶缓缓流过全身，带走所有紧张。感受身体逐渐沉重，让睡意自然降临。"),
    ],
    script="请找一个舒适的姿势坐好或躺下，轻轻闭上眼睛。让我们开始深呼吸练习。用鼻子慢慢吸气，一、二、三、四，感受腹部慢慢鼓起。屏住呼吸，一、二、三、四。然后用嘴慢慢呼气，一、二、三、四、五、六，让所有的紧张随呼气流出。非常好，我们再来几次。吸气...屏息...呼气...现在，想象一道温暖的光芒从你的头顶缓缓流过，经过额头、眼睛、脸颊、脖子、肩膀...流过整个身体，带走所有的紧张和疲惫。感受你的身体越来越沉重，越来越放松。让这份宁静伴随你进入梦乡。晚安。",
)


def _text_contains_terms(text: str, terms: list[str]) -> bool:
    for term in terms:
        if term in text:
            return True
    return False


def validate_routine(routine: SleepRoutine) -> bool:
    fields_to_check = [routine.strategy, routine.script]
    for step in routine.steps:
        fields_to_check.append(step.instruction)

    for text in fields_to_check:
        if _text_contains_terms(text, MEDICAL_TERMS + DRUG_TERMS):
            return False
    return True


def _build_context(
    checkin: CheckinRequest,
    db: Session,
    history_days: int,
) -> RoutineGenerationContext:
    logs = sleep_log_repo.get_recent_logs(db, history_days)
    record_count = len(logs)

    if record_count > 0:
        avg_latency = round(sum(l.sleep_latency_minutes for l in logs) / record_count, 1)
        avg_awakenings = round(sum(l.awakenings for l in logs) / record_count, 1)
        avg_quality = round(sum(l.sleep_quality for l in logs) / record_count, 1)
        avg_stress = round(sum(l.stress_level for l in logs) / record_count, 1)
        avg_screen = round(sum(l.screen_time_minutes for l in logs) / record_count, 1)
    else:
        avg_latency = avg_awakenings = avg_quality = avg_stress = avg_screen = None

    return RoutineGenerationContext(
        mood=checkin.mood,
        energy_level=checkin.energy_level,
        stress_level=checkin.stress_level,
        caffeine_after_3pm=checkin.caffeine_after_3pm,
        screen_time_minutes=checkin.screen_time_minutes,
        available_minutes=checkin.available_minutes,
        preferred_audio=checkin.preferred_audio,
        notes=checkin.notes,
        history_available=record_count > 0,
        avg_latency=avg_latency,
        avg_awakenings=avg_awakenings,
        avg_quality=avg_quality,
        avg_stress=avg_stress,
        avg_screen=avg_screen,
        record_count=record_count,
    )


def _make_meta(
    *,
    history_available: bool,
    record_count: int,
    generation_mode: str,
) -> RoutineMeta:
    return RoutineMeta(
        history_available=history_available,
        history_record_count=record_count,
        generation_mode=generation_mode,
        generated_at=datetime.now(timezone.utc),
    )


def _generate_with_provider(
    provider: LLMProvider,
    ctx: RoutineGenerationContext,
    max_retries: int = 1,
) -> SleepRoutine:
    last_error: Exception | None = None
    for attempt in range(1 + max_retries):
        try:
            routine = provider.generate(ctx)
            if validate_routine(routine):
                return routine
            last_error = ProviderError("Safety validation failed")
        except ProviderTimeoutError:
            raise
        except ProviderError as e:
            last_error = e
    raise last_error or ProviderError("Generation failed")


def generate_routine(
    checkin: CheckinRequest,
    db: Session,
    history_days: int = 7,
):
    ctx = _build_context(checkin, db, history_days)
    meta = _make_meta(
        history_available=ctx.history_available,
        record_count=ctx.record_count,
        generation_mode="mock",
    )

    crisis_level = detect_crisis_level(checkin.notes)

    if crisis_level == CrisisLevel.CRISIS:
        meta.generation_mode = "rule_based"
        return SafetyRedirectResponse(
            message="感谢你的信任。我注意到你可能正在经历一些困难时刻。请记住，你并不孤单，专业的帮助就在身边。",
            resources=DEFAULT_RESOURCES,
            immediate_actions=[
                "如果你正处于紧急危险中，请拨打 110 或前往最近的急诊室",
                "联系你信任的家人或朋友，告诉他们你的感受",
                "尝试深呼吸，缓慢吸气4秒，呼气6秒，重复几次",
            ],
            meta=meta,
        )

    if crisis_level == CrisisLevel.DISTRESS:
        meta.generation_mode = "rule_based"
        return SupportiveClarificationResponse(
            message="我听到了你的感受。这些情绪是正常的，你愿意多说一些吗？无论如何，我会在这里陪伴你。",
            resources=DEFAULT_RESOURCES,
            meta=meta,
        )

    provider = get_provider()
    try:
        routine = _generate_with_provider(provider, ctx)
        meta.generation_mode = "mock" if settings.LLM_MODE == "mock" else "real"
        return RoutineSuccessResponse(
            routine=routine,
            safety_notice=SAFETY_NOTICE,
            meta=meta,
        )
    except ProviderTimeoutError:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="LLM 服务暂时不可用，请稍后重试")
    except Exception:
        meta.generation_mode = "fallback"
        return RoutineSuccessResponse(
            routine=FALLBACK_ROUTINE,
            safety_notice=SAFETY_NOTICE,
            meta=meta,
        )


from app.core.config import settings  # noqa: E402


_graph_cache = None


def _get_compiled_graph():
    global _graph_cache
    if _graph_cache is None:
        from app.agents.graph import build_graph

        _graph_cache = build_graph()
    return _graph_cache


def generate_routine_via_graph(
    checkin: CheckinRequest,
    db: Session,
    history_days: int = 7,
):
    from fastapi import HTTPException

    from app.agents.runtime import AgentRuntimeContext

    graph = _get_compiled_graph()
    provider = get_provider()
    ctx = AgentRuntimeContext(db=db, provider=provider)

    try:
        result = graph.invoke(
            {"checkin": checkin, "history_days": history_days},
            context=ctx,
            recursion_limit=12,
        )
    except ProviderTimeoutError:
        raise HTTPException(
            status_code=503, detail="LLM 服务暂时不可用，请稍后重试"
        )

    return result["response"]
