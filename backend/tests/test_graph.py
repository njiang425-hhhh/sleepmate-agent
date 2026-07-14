from datetime import date, time
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.domain.crisis_detector import CrisisLevel, detect_crisis_level
from app.agents.domain.history_analyzer import analyze_history
from app.agents.domain.safety_validator import validate_routine
from app.agents.graph import build_graph
from app.agents.nodes import (
    FALLBACK_ROUTINE,
    analyze_safety_node,
    build_fallback_node,
    build_safety_redirect_node,
    build_supportive_response_node,
    finalize_response_node,
    generate_routine_node,
    increment_retry_node,
    initialize_state_node,
    retrieve_history_node,
    safety_check_node,
)
from app.agents.runtime import AgentRuntimeContext
from app.agents.state import AgentState
from app.core.database import Base, get_db
from app.main import app
from app.models.sleep_log import SleepLog
from app.schemas.routine import (
    RoutineMeta,
    RoutineStep,
    SleepRoutine,
)
from app.services.llm_provider import (
    LLMProvider,
    MockLLMProvider,
    ProviderError,
    ProviderRefusedError,
    ProviderTimeoutError,
    RoutineGenerationContext,
)

# ---------- test database setup ----------

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_module():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=TEST_ENGINE)


def teardown_module():
    Base.metadata.drop_all(bind=TEST_ENGINE)


def _fresh_db():
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    return TestSessionLocal()


def _insert_log(db, log_date, **overrides):
    defaults = dict(
        log_date=log_date,
        bedtime=time(23, 0),
        wake_time=time(7, 0),
        sleep_latency_minutes=20,
        awakenings=1,
        sleep_quality=3,
        mood_before_sleep="relaxed",
        stress_level=4,
        caffeine_after_3pm=False,
        screen_time_minutes=30,
    )
    defaults.update(overrides)
    log = SleepLog(**defaults)
    db.add(log)
    db.commit()
    return log


VALID_CHECKIN = {
    "mood": "relaxed",
    "energy_level": 5,
    "stress_level": 4,
    "caffeine_after_3pm": False,
    "screen_time_minutes": 30,
    "available_minutes": 15,
    "preferred_audio": "rain",
}


def _make_runtime(db=None, provider=None):
    if db is None:
        db = _fresh_db()
    if provider is None:
        provider = MockLLMProvider()
    return MagicMock(context=AgentRuntimeContext(db=db, provider=provider))


def _make_state(**overrides):
    state: AgentState = {
        "checkin": VALID_CHECKIN,
        "history_days": 7,
    }
    state.update(overrides)
    return state


# ============================================================
# Domain unit tests
# ============================================================


class TestCrisisDetector:
    def test_crisis_explicit(self):
        assert detect_crisis_level("我想自杀") == CrisisLevel.CRISIS

    def test_crisis_no_will_to_live(self):
        assert detect_crisis_level("活不下去了") == CrisisLevel.CRISIS

    def test_distress_vague_pain(self):
        assert detect_crisis_level("太痛苦了，受不了了") == CrisisLevel.DISTRESS

    def test_distress_tired(self):
        assert detect_crisis_level("好累") == CrisisLevel.DISTRESS

    def test_none_normal_notes(self):
        assert detect_crisis_level("今天工作压力大") == CrisisLevel.NONE

    def test_none_empty(self):
        assert detect_crisis_level(None) == CrisisLevel.NONE

    def test_none_empty_string(self):
        assert detect_crisis_level("") == CrisisLevel.NONE

    def test_negation_not_crisis(self):
        assert detect_crisis_level("我不想死") == CrisisLevel.NONE

    def test_quotation_not_crisis(self):
        assert detect_crisis_level("电影里的角色想死") == CrisisLevel.NONE


class TestSafetyValidator:
    def test_valid_routine_passes(self):
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="深呼吸放松",
            steps=[
                RoutineStep(
                    order=1,
                    action="呼吸",
                    duration_seconds=60,
                    instruction="缓慢深呼吸",
                )
            ],
            script="请深呼吸",
        )
        assert validate_routine(routine) is True

    def test_medical_term_fails(self):
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="建议使用褪黑素",
            steps=[
                RoutineStep(
                    order=1,
                    action="test",
                    duration_seconds=30,
                    instruction="test",
                )
            ],
            script="test script",
        )
        assert validate_routine(routine) is False

    def test_drug_term_in_script_fails(self):
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="放松",
            steps=[
                RoutineStep(
                    order=1,
                    action="test",
                    duration_seconds=30,
                    instruction="test",
                )
            ],
            script="建议服用安眠药",
        )
        assert validate_routine(routine) is False


class TestHistoryAnalyzer:
    def test_empty_logs(self):
        result = analyze_history([])
        assert result["history_available"] is False
        assert result["record_count"] == 0
        assert result["avg_latency"] is None

    def test_with_logs(self):
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10), sleep_latency_minutes=10)
        _insert_log(db, date(2026, 7, 11), sleep_latency_minutes=20)
        logs = db.query(SleepLog).all()
        result = analyze_history(logs)
        assert result["history_available"] is True
        assert result["record_count"] == 2
        assert result["avg_latency"] == 15.0
        db.close()


# ============================================================
# Node unit tests
# ============================================================


class TestInitializeStateNode:
    def test_sets_defaults(self):
        runtime = _make_runtime()
        state = _make_state()
        result = initialize_state_node(state, runtime=runtime)
        assert result["crisis_level"] == "none"
        assert result["retry_count"] == 0
        assert result["routine"] is None
        assert result["response"] is None
        assert result["history_available"] is False
        assert result["record_count"] == 0


class TestAnalyzeSafetyNode:
    def test_crisis(self):
        runtime = _make_runtime()
        state = _make_state(checkin={**VALID_CHECKIN, "notes": "我想自杀"})
        result = analyze_safety_node(state, runtime=runtime)
        assert result["crisis_level"] == "crisis"

    def test_distress(self):
        runtime = _make_runtime()
        state = _make_state(checkin={**VALID_CHECKIN, "notes": "太痛苦了"})
        result = analyze_safety_node(state, runtime=runtime)
        assert result["crisis_level"] == "distress"

    def test_none(self):
        runtime = _make_runtime()
        state = _make_state(checkin={**VALID_CHECKIN, "notes": "今天还不错"})
        result = analyze_safety_node(state, runtime=runtime)
        assert result["crisis_level"] == "none"

    def test_none_no_notes(self):
        runtime = _make_runtime()
        state = _make_state(checkin={k: v for k, v in VALID_CHECKIN.items() if k != "notes"})
        result = analyze_safety_node(state, runtime=runtime)
        assert result["crisis_level"] == "none"


class TestBuildSafetyRedirectNode:
    def test_builds_response(self):
        runtime = _make_runtime()
        state = _make_state(crisis_level="crisis")
        result = build_safety_redirect_node(state, runtime=runtime)
        assert result["response"].type == "safety_redirect"
        assert result["generation_mode"] == "rule_based"
        assert len(result["response"].immediate_actions) > 0


class TestBuildSupportiveResponseNode:
    def test_builds_response(self):
        runtime = _make_runtime()
        state = _make_state(crisis_level="distress")
        result = build_supportive_response_node(state, runtime=runtime)
        assert result["response"].type == "supportive_clarification"
        assert result["generation_mode"] == "rule_based"


class TestRetrieveHistoryNode:
    def test_with_logs(self):
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        _insert_log(db, date(2026, 7, 11))
        _insert_log(db, date(2026, 7, 12))
        runtime = _make_runtime(db=db)
        state = _make_state()
        result = retrieve_history_node(state, runtime=runtime)
        assert result["history_available"] is True
        assert result["record_count"] == 3
        db.close()

    def test_empty(self):
        db = _fresh_db()
        runtime = _make_runtime(db=db)
        state = _make_state()
        result = retrieve_history_node(state, runtime=runtime)
        assert result["history_available"] is False
        assert result["record_count"] == 0
        db.close()


class TestGenerateRoutineNode:
    def test_success(self):
        runtime = _make_runtime(provider=MockLLMProvider())
        state = _make_state()
        result = generate_routine_node(state, runtime=runtime)
        assert result["routine"] is not None
        assert result["generation_mode"] == "mock"

    def test_provider_error_returns_none(self):
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=ProviderError("fail"))
        runtime = _make_runtime(provider=provider)
        state = _make_state()
        result = generate_routine_node(state, runtime=runtime)
        assert result["routine"] is None

    def test_timeout_raises(self):
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=ProviderTimeoutError("timeout"))
        runtime = _make_runtime(provider=provider)
        state = _make_state()
        with pytest.raises(ProviderTimeoutError):
            generate_routine_node(state, runtime=runtime)

    def test_unknown_error_propagates(self):
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=RuntimeError("unknown"))
        runtime = _make_runtime(provider=provider)
        state = _make_state()
        with pytest.raises(RuntimeError):
            generate_routine_node(state, runtime=runtime)


class TestSafetyCheckNode:
    def test_pass(self):
        runtime = _make_runtime()
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="深呼吸",
            steps=[
                RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
            ],
            script="test script",
        )
        state = _make_state(routine=routine)
        result = safety_check_node(state, runtime=runtime)
        assert result["safety_passed"] is True

    def test_fail_unsafe(self):
        runtime = _make_runtime()
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="建议使用褪黑素",
            steps=[
                RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
            ],
            script="test",
        )
        state = _make_state(routine=routine)
        result = safety_check_node(state, runtime=runtime)
        assert result["safety_passed"] is False

    def test_fail_none_routine(self):
        runtime = _make_runtime()
        state = _make_state(routine=None)
        result = safety_check_node(state, runtime=runtime)
        assert result["safety_passed"] is False


class TestIncrementRetryNode:
    def test_increments(self):
        runtime = _make_runtime()
        state = _make_state(retry_count=0)
        result = increment_retry_node(state, runtime=runtime)
        assert result["retry_count"] == 1

    def test_from_default(self):
        runtime = _make_runtime()
        state = _make_state()
        result = increment_retry_node(state, runtime=runtime)
        assert result["retry_count"] == 1


class TestBuildFallbackNode:
    def test_sets_fallback(self):
        runtime = _make_runtime()
        state = _make_state()
        result = build_fallback_node(state, runtime=runtime)
        assert result["routine"] == FALLBACK_ROUTINE
        assert result["generation_mode"] == "fallback"


class TestFinalizeResponseNode:
    def test_existing_response_passthrough(self):
        runtime = _make_runtime()
        from app.schemas.routine import SafetyRedirectResponse

        existing = SafetyRedirectResponse(
            message="test",
            resources=[],
            immediate_actions=[],
            meta=RoutineMeta(
                history_available=False,
                history_record_count=0,
                generation_mode="rule_based",
                generated_at="2026-01-01T00:00:00Z",
            ),
        )
        state = _make_state(response=existing)
        result = finalize_response_node(state, runtime=runtime)
        assert result == {}

    def test_builds_success_response(self):
        runtime = _make_runtime()
        routine = SleepRoutine(
            title="test",
            duration_minutes=5,
            strategy="放松",
            steps=[
                RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
            ],
            script="test",
        )
        state = _make_state(
            routine=routine,
            generation_mode="mock",
            history_available=True,
            record_count=3,
        )
        result = finalize_response_node(state, runtime=runtime)
        resp = result["response"]
        assert resp.type == "success"
        assert resp.meta.generation_mode == "mock"
        assert resp.meta.history_available is True
        assert resp.meta.history_record_count == 3


# ============================================================
# Full graph integration tests
# ============================================================


class TestGraphCrisisPath:
    def test_crisis_returns_safety_redirect(self):
        graph = build_graph()
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": {**VALID_CHECKIN, "notes": "我想自杀"}, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "safety_redirect"
        assert result["response"].meta.generation_mode == "rule_based"

    def test_crisis_does_not_query_db(self):
        graph = build_graph()
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        with patch("app.agents.nodes.sleep_log_repo") as mock_repo:
            result = graph.invoke(
                {"checkin": {**VALID_CHECKIN, "notes": "我想自杀"}, "history_days": 7},
                context=ctx,
                recursion_limit=12,
            )
            mock_repo.get_recent_logs.assert_not_called()

        assert result["response"].type == "safety_redirect"

    def test_crisis_does_not_call_provider(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        original_generate = provider.generate
        ctx = AgentRuntimeContext(db=db, provider=provider)

        with patch.object(provider, "generate") as mock_gen:
            result = graph.invoke(
                {"checkin": {**VALID_CHECKIN, "notes": "我想自杀"}, "history_days": 7},
                context=ctx,
                recursion_limit=12,
            )
            mock_gen.assert_not_called()

        assert result["response"].type == "safety_redirect"


class TestGraphDistressPath:
    def test_distress_returns_supportive(self):
        graph = build_graph()
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": {**VALID_CHECKIN, "notes": "太痛苦了"}, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "supportive_clarification"
        assert result["response"].meta.generation_mode == "rule_based"

    def test_distress_does_not_query_db(self):
        graph = build_graph()
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        with patch("app.agents.nodes.sleep_log_repo") as mock_repo:
            result = graph.invoke(
                {"checkin": {**VALID_CHECKIN, "notes": "太痛苦了"}, "history_days": 7},
                context=ctx,
                recursion_limit=12,
            )
            mock_repo.get_recent_logs.assert_not_called()

        assert result["response"].type == "supportive_clarification"

    def test_distress_does_not_call_provider(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        with patch.object(provider, "generate") as mock_gen:
            result = graph.invoke(
                {"checkin": {**VALID_CHECKIN, "notes": "太痛苦了"}, "history_days": 7},
                context=ctx,
                recursion_limit=12,
            )
            mock_gen.assert_not_called()

        assert result["response"].type == "supportive_clarification"


class TestGraphNormalPath:
    def test_with_history(self):
        graph = build_graph()
        db = _fresh_db()
        _insert_log(db, date(2026, 7, 10))
        _insert_log(db, date(2026, 7, 11))
        _insert_log(db, date(2026, 7, 12))
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].meta.history_available is True
        assert result["response"].meta.history_record_count == 3
        assert result["response"].meta.generation_mode == "mock"

    def test_no_history(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].meta.history_available is False
        assert result["response"].meta.history_record_count == 0


class TestGraphRetryAndFallback:
    def test_provider_error_retry_then_success(self):
        graph = build_graph()
        db = _fresh_db()
        call_count = 0

        class FlakyProvider(LLMProvider):
            @property
            def mode(self):
                return "mock"

            def generate(self, ctx):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ProviderError("first fail")
                return SleepRoutine(
                    title="retry success",
                    duration_minutes=5,
                    strategy="放松",
                    steps=[
                        RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
                    ],
                    script="test script",
                )

        provider = FlakyProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].routine.title == "retry success"
        assert call_count == 2

    def test_provider_error_retry_then_fallback(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=ProviderError("always fail"))
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].routine.title == "呼吸引导放松"
        assert result["response"].meta.generation_mode == "fallback"

    def test_safety_fail_retry_then_success(self):
        graph = build_graph()
        db = _fresh_db()
        call_count = 0

        class UnsafeThenSafeProvider(LLMProvider):
            @property
            def mode(self):
                return "mock"

            def generate(self, ctx):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return SleepRoutine(
                        title="unsafe",
                        duration_minutes=5,
                        strategy="建议使用褪黑素",
                        steps=[
                            RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
                        ],
                        script="test",
                    )
                return SleepRoutine(
                    title="safe",
                    duration_minutes=5,
                    strategy="深呼吸放松",
                    steps=[
                        RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
                    ],
                    script="test script",
                )

        provider = UnsafeThenSafeProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].routine.title == "safe"
        assert call_count == 2

    def test_safety_fail_retry_then_fallback(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        provider.generate = MagicMock(
            return_value=SleepRoutine(
                title="always unsafe",
                duration_minutes=5,
                strategy="建议使用褪黑素",
                steps=[
                    RoutineStep(order=1, action="test", duration_seconds=30, instruction="test")
                ],
                script="test",
            )
        )
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].type == "success"
        assert result["response"].routine.title == "呼吸引导放松"
        assert result["response"].meta.generation_mode == "fallback"


class TestGraphTimeout:
    def test_timeout_does_not_fallback(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=ProviderTimeoutError("timeout"))
        ctx = AgentRuntimeContext(db=db, provider=provider)

        with pytest.raises(ProviderTimeoutError):
            graph.invoke(
                {"checkin": VALID_CHECKIN, "history_days": 7},
                context=ctx,
                recursion_limit=12,
            )


class TestGraphOutput:
    def test_output_only_response(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert "response" in result
        assert result["response"] is not None


class TestGraphGenerationMode:
    def test_mock_mode(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].meta.generation_mode == "mock"

    def test_rule_based_mode_crisis(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": {**VALID_CHECKIN, "notes": "我想自杀"}, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].meta.generation_mode == "rule_based"

    def test_fallback_mode(self):
        graph = build_graph()
        db = _fresh_db()
        provider = MockLLMProvider()
        provider.generate = MagicMock(side_effect=ProviderError("fail"))
        ctx = AgentRuntimeContext(db=db, provider=provider)

        result = graph.invoke(
            {"checkin": VALID_CHECKIN, "history_days": 7},
            context=ctx,
            recursion_limit=12,
        )

        assert result["response"].meta.generation_mode == "fallback"
