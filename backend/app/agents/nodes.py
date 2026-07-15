from datetime import datetime, timezone

from langgraph.runtime import Runtime

from app.agents.domain.crisis_detector import detect_crisis_level
from app.agents.domain.history_analyzer import analyze_history
from app.agents.domain.safety_validator import validate_routine
from app.agents.runtime import AgentRuntimeContext
from app.agents.state import AgentState
from app.repositories import sleep_log_repo
from app.schemas.routine import (
    RoutineMeta,
    RoutineSuccessResponse,
    SafetyRedirectResponse,
    SleepRoutine,
    SupportiveClarificationResponse,
)
from app.schemas.checkin import CheckinRequest
from app.schemas.knowledge import KnowledgeContext
from app.services.embedding_provider import EmbeddingUnavailableError
from app.services.llm_provider import (
    ProviderError,
    ProviderTimeoutError,
    RoutineGenerationContext,
)
from app.services.safety_resources import DEFAULT_RESOURCES

SAFETY_NOTICE = "本计划仅供参考，不替代专业医疗建议。如有持续睡眠问题，请咨询医生。"

FALLBACK_ROUTINE = SleepRoutine(
    title="呼吸引导放松",
    duration_minutes=5,
    strategy="基础呼吸引导，帮助身心放松",
    steps=[
        {
            "order": 1,
            "action": "准备就位",
            "duration_seconds": 30,
            "instruction": "找一个舒适的姿势坐好或躺下，轻轻闭上眼睛，将双手自然放在身体两侧。",
        },
        {
            "order": 2,
            "action": "深呼吸练习",
            "duration_seconds": 180,
            "instruction": '用鼻子缓慢吸气4秒，感受腹部隆起；屏息4秒；用嘴缓慢呼气6秒。重复6次，每次呼气时默念"放松"。',
        },
        {
            "order": 3,
            "action": "放松收尾",
            "duration_seconds": 90,
            "instruction": "保持自然呼吸，想象温暖的光芒从头顶缓缓流过全身，带走所有紧张。感受身体逐渐沉重，让睡意自然降临。",
        },
    ],
    script=(
        "请找一个舒适的姿势坐好或躺下，轻轻闭上眼睛。让我们开始深呼吸练习。"
        "用鼻子慢慢吸气，一、二、三、四，感受腹部慢慢鼓起。"
        "屏住呼吸，一、二、三、四。"
        "然后用嘴慢慢呼气，一、二、三、四、五、六，让所有的紧张随呼气流出。"
        "非常好，我们再来几次。吸气...屏息...呼气..."
        "现在，想象一道温暖的光芒从你的头顶缓缓流过，经过额头、眼睛、脸颊、脖子、肩膀..."
        "流过整个身体，带走所有的紧张和疲惫。"
        "感受你的身体越来越沉重，越来越放松。让这份宁静伴随你进入梦乡。晚安。"
    ),
)


def _get_checkin(state: AgentState) -> CheckinRequest:
    checkin = state["checkin"]
    if isinstance(checkin, dict):
        return CheckinRequest(**checkin)
    return checkin


def _build_context(state: AgentState) -> RoutineGenerationContext:
    checkin = _get_checkin(state)
    kctx = state.get("knowledge_context")
    return RoutineGenerationContext(
        mood=checkin.mood,
        energy_level=checkin.energy_level,
        stress_level=checkin.stress_level,
        caffeine_after_3pm=checkin.caffeine_after_3pm,
        screen_time_minutes=checkin.screen_time_minutes,
        available_minutes=checkin.available_minutes,
        preferred_audio=checkin.preferred_audio,
        notes=checkin.notes,
        history_available=state.get("history_available", False),
        avg_latency=state.get("avg_latency"),
        avg_awakenings=state.get("avg_awakenings"),
        avg_quality=state.get("avg_quality"),
        avg_stress=state.get("avg_stress"),
        avg_screen=state.get("avg_screen"),
        record_count=state.get("record_count", 0),
        knowledge_chunks=kctx.chunks if kctx else [],
    )


def initialize_state_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    return {
        "checkin": state["checkin"],
        "history_days": state["history_days"],
        "crisis_level": "none",
        "history_available": False,
        "record_count": 0,
        "avg_latency": None,
        "avg_awakenings": None,
        "avg_quality": None,
        "avg_stress": None,
        "avg_screen": None,
        "knowledge_context": None,
        "routine": None,
        "retry_count": 0,
        "response": None,
    }


def analyze_safety_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    checkin = _get_checkin(state)
    notes = checkin.notes
    level = detect_crisis_level(notes)
    return {"crisis_level": level.value}


def route_after_safety(state: AgentState) -> str:
    return state["crisis_level"]


def build_safety_redirect_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    meta = RoutineMeta(
        history_available=False,
        history_record_count=0,
        generation_mode="rule_based",
        generated_at=datetime.now(timezone.utc),
    )
    response = SafetyRedirectResponse(
        message="感谢你的信任。我注意到你可能正在经历一些困难时刻。请记住，你并不孤单，专业的帮助就在身边。",
        resources=DEFAULT_RESOURCES,
        immediate_actions=[
            "如果你正处于紧急危险中，请拨打 110 或前往最近的急诊室",
            "联系你信任的家人或朋友，告诉他们你的感受",
            "尝试深呼吸，缓慢吸气4秒，呼气6秒，重复几次",
        ],
        meta=meta,
    )
    return {"response": response, "generation_mode": "rule_based"}


def build_supportive_response_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    meta = RoutineMeta(
        history_available=False,
        history_record_count=0,
        generation_mode="rule_based",
        generated_at=datetime.now(timezone.utc),
    )
    response = SupportiveClarificationResponse(
        message="我听到了你的感受。这些情绪是正常的，你愿意多说一些吗？无论如何，我会在这里陪伴你。",
        resources=DEFAULT_RESOURCES,
        meta=meta,
    )
    return {"response": response, "generation_mode": "rule_based"}


def retrieve_history_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    db = runtime.context.db
    history_days = state["history_days"]
    logs = sleep_log_repo.get_recent_logs(db, history_days)
    return analyze_history(logs)


def retrieve_sleep_knowledge_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    """从 RAG 知识库检索相关助眠知识. 优雅降级."""
    rag_service = runtime.context.rag_service

    if rag_service is None:
        return {"knowledge_context": KnowledgeContext(status="disabled")}

    try:
        checkin = _get_checkin(state)
        history_stats = None
        if state.get("history_available"):
            history_stats = {
                "avg_stress": state.get("avg_stress"),
                "avg_latency": state.get("avg_latency"),
            }
        ctx = rag_service.retrieve(checkin, history_stats)
        return {"knowledge_context": ctx}
    except EmbeddingUnavailableError:
        return {"knowledge_context": KnowledgeContext(status="unavailable")}
    except Exception:
        return {"knowledge_context": KnowledgeContext(status="unavailable")}


def generate_routine_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    provider = runtime.context.provider
    ctx = _build_context(state)

    try:
        routine = provider.generate(ctx)
        return {"routine": routine, "generation_mode": provider.mode}
    except ProviderTimeoutError:
        raise
    except ProviderError:
        return {"routine": None}


def safety_check_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    routine = state.get("routine")
    if routine is None:
        return {"safety_passed": False}
    return {"safety_passed": validate_routine(routine)}


def route_after_safety_check(state: AgentState) -> str:
    if state.get("safety_passed", False):
        return "pass"
    if state.get("retry_count", 0) < 1:
        return "retry"
    return "fallback"


def increment_retry_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    return {"retry_count": state.get("retry_count", 0) + 1}


def build_fallback_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    return {
        "routine": FALLBACK_ROUTINE,
        "generation_mode": "fallback",
    }


def finalize_response_node(
    state: AgentState, *, runtime: Runtime[AgentRuntimeContext]
) -> dict:
    if state.get("response") is not None:
        return {}

    routine = state["routine"]
    generation_mode = state.get("generation_mode", "mock")

    kctx = state.get("knowledge_context")
    rag_status = "disabled"
    knowledge_sources: list[str] = []
    if kctx is not None:
        status = kctx.status
        rag_status = "success" if status == "used" else status if status in ("empty", "unavailable", "disabled") else "error"
        knowledge_sources = list({c.source for c in kctx.chunks})

    meta = RoutineMeta(
        history_available=state.get("history_available", False),
        history_record_count=state.get("record_count", 0),
        generation_mode=generation_mode,
        generated_at=datetime.now(timezone.utc),
        rag_status=rag_status,
        knowledge_sources=knowledge_sources,
    )

    return {
        "response": RoutineSuccessResponse(
            routine=routine,
            safety_notice=SAFETY_NOTICE,
            meta=meta,
        )
    }
