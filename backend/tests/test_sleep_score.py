import pytest

from app.services.sleep_score_service import (
    SleepScoreInput,
    calculate_sleep_score,
    _score_latency,
    _score_awakenings,
    _score_quality,
    _score_stress,
    _score_screen,
)


def _make_input(**kwargs) -> SleepScoreInput:
    defaults = {
        "sleep_latency_minutes": 15,
        "awakenings": 1,
        "sleep_quality": 3,
        "stress_level": 5,
        "screen_time_minutes": 30,
    }
    defaults.update(kwargs)
    return SleepScoreInput(**defaults)


# ---------- Full score integration tests ----------


def test_perfect_score():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=5, awakenings=0, sleep_quality=5,
        stress_level=1, screen_time_minutes=0,
    ))
    assert result.score == 100
    assert result.level == "excellent"
    assert result.level_label == "优秀"


def test_good_score():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=20, awakenings=1, sleep_quality=4,
        stress_level=3, screen_time_minutes=15,
    ))
    assert result.score == 79
    assert result.level == "good"
    assert result.level_label == "良好"


def test_poor_score():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=35, awakenings=2, sleep_quality=3,
        stress_level=6, screen_time_minutes=45,
    ))
    assert result.score == 54
    assert result.level == "poor"
    assert result.level_label == "较差"


def test_very_poor_score():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=50, awakenings=4, sleep_quality=2,
        stress_level=8, screen_time_minutes=90,
    ))
    assert result.score == 24
    assert result.level == "very_poor"
    assert result.level_label == "很差"


def test_zero_score():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=90, awakenings=6, sleep_quality=1,
        stress_level=10, screen_time_minutes=120,
    ))
    assert result.score == 0
    assert result.level == "very_poor"


def test_boundary_latency_15():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=15, awakenings=0, sleep_quality=5,
        stress_level=2, screen_time_minutes=0,
    ))
    assert result.score == 100


def test_boundary_latency_30():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=30, awakenings=2, sleep_quality=3,
        stress_level=5, screen_time_minutes=30,
    ))
    assert result.score == 64
    assert result.level == "fair"


def test_single_bad_stress():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=10, awakenings=0, sleep_quality=4,
        stress_level=9, screen_time_minutes=0,
    ))
    assert result.score == 75
    assert result.level == "good"


def test_single_bad_screen():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=8, awakenings=0, sleep_quality=5,
        stress_level=2, screen_time_minutes=90,
    ))
    assert result.score == 85
    assert result.level == "good"


def test_multi_bad_dimensions():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=40, awakenings=3, sleep_quality=2,
        stress_level=7, screen_time_minutes=70,
    ))
    assert result.score == 29
    assert result.level == "very_poor"


# ---------- Parameterized scoring tests ----------


@pytest.mark.parametrize("minutes,expected", [
    (0, 20), (15, 20), (16, 15), (30, 15), (31, 10), (45, 10),
    (46, 5), (60, 5), (61, 0), (120, 0),
])
def test_latency_scoring(minutes, expected):
    assert _score_latency(minutes) == expected


@pytest.mark.parametrize("count,expected", [
    (0, 20), (1, 16), (2, 12), (3, 6), (4, 6), (5, 0), (20, 0),
])
def test_awakenings_scoring(count, expected):
    assert _score_awakenings(count) == expected


@pytest.mark.parametrize("quality,expected", [
    (1, 0), (2, 7), (3, 14), (4, 20), (5, 25),
])
def test_quality_scoring(quality, expected):
    assert _score_quality(quality) == expected


@pytest.mark.parametrize("level,expected", [
    (1, 20), (2, 20), (3, 16), (4, 16), (5, 11),
    (6, 11), (7, 6), (8, 6), (9, 0), (10, 0),
])
def test_stress_scoring(level, expected):
    assert _score_stress(level) == expected


@pytest.mark.parametrize("minutes,expected", [
    (0, 15), (1, 12), (30, 12), (31, 7), (60, 7), (61, 0), (300, 0),
])
def test_screen_scoring(minutes, expected):
    assert _score_screen(minutes) == expected


# ---------- Breakdown structure ----------


def test_breakdown_keys():
    result = calculate_sleep_score(_make_input())
    expected_keys = {"latency", "awakenings", "quality", "stress", "screen"}
    assert set(result.breakdown.keys()) == expected_keys
    for key, item in result.breakdown.items():
        assert "score" in item
        assert "max_score" in item
        assert "label" in item


def test_breakdown_max_scores():
    result = calculate_sleep_score(_make_input())
    assert result.breakdown["latency"]["max_score"] == 20
    assert result.breakdown["awakenings"]["max_score"] == 20
    assert result.breakdown["quality"]["max_score"] == 25
    assert result.breakdown["stress"]["max_score"] == 20
    assert result.breakdown["screen"]["max_score"] == 15


# ---------- Advice tests ----------


def test_advice_perfect():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=5, awakenings=0, sleep_quality=5,
        stress_level=1, screen_time_minutes=0,
    ))
    assert len(result.advice) == 1
    assert result.advice[0] == "睡眠状态非常好，继续保持！"


def test_advice_level_first():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=50, awakenings=0, sleep_quality=4,
        stress_level=3, screen_time_minutes=0,
    ))
    assert result.advice[0] == "睡眠质量不错，有小幅优化空间。"
    assert any("入睡耗时" in a for a in result.advice)


def test_advice_no_duplicates():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=50, awakenings=3, sleep_quality=2,
        stress_level=9, screen_time_minutes=80,
    ))
    assert len(result.advice) == len(set(result.advice))


def test_advice_max_5():
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=50, awakenings=5, sleep_quality=1,
        stress_level=10, screen_time_minutes=100,
    ))
    assert len(result.advice) <= 5


def test_advice_latency():
    result = calculate_sleep_score(_make_input(sleep_latency_minutes=50))
    assert any("入睡耗时超过 45 分钟" in a for a in result.advice)


def test_advice_awakenings():
    result = calculate_sleep_score(_make_input(awakenings=3))
    assert any("夜间醒来频繁" in a for a in result.advice)


def test_advice_quality():
    result = calculate_sleep_score(_make_input(sleep_quality=2))
    assert any("自评睡眠质量较低" in a for a in result.advice)


def test_advice_stress():
    result = calculate_sleep_score(_make_input(stress_level=9))
    assert any("压力水平偏高" in a for a in result.advice)


def test_advice_screen():
    result = calculate_sleep_score(_make_input(screen_time_minutes=80))
    assert any("睡前屏幕时间过长" in a for a in result.advice)


def test_advice_trend_based():
    """Trend advice should also follow dedup + max 5 rule."""
    result = calculate_sleep_score(_make_input(
        sleep_latency_minutes=50, awakenings=3, sleep_quality=2,
        stress_level=9, screen_time_minutes=80,
    ))
    assert len(result.advice) <= 5
    assert len(result.advice) == len(set(result.advice))
