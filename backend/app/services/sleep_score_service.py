from pydantic import BaseModel, Field


class SleepScoreInput(BaseModel):
    sleep_latency_minutes: int = Field(ge=0)
    awakenings: int = Field(ge=0)
    sleep_quality: int = Field(ge=1, le=5)
    stress_level: int = Field(ge=1, le=10)
    screen_time_minutes: int = Field(ge=0)


class SleepScoreResult(BaseModel):
    score: int
    level: str
    level_label: str
    advice: list[str]
    breakdown: dict[str, dict]


def _score_latency(minutes: int) -> int:
    if minutes <= 15:
        return 20
    if minutes <= 30:
        return 15
    if minutes <= 45:
        return 10
    if minutes <= 60:
        return 5
    return 0


def _score_awakenings(count: int) -> int:
    if count == 0:
        return 20
    if count == 1:
        return 16
    if count == 2:
        return 12
    if count <= 4:
        return 6
    return 0


def _score_quality(quality: int) -> int:
    mapping = {5: 25, 4: 20, 3: 14, 2: 7, 1: 0}
    return mapping[quality]


def _score_stress(level: int) -> int:
    if level <= 2:
        return 20
    if level <= 4:
        return 16
    if level <= 6:
        return 11
    if level <= 8:
        return 6
    return 0


def _score_screen(minutes: int) -> int:
    if minutes == 0:
        return 15
    if minutes <= 30:
        return 12
    if minutes <= 60:
        return 7
    return 0


def _get_level(score: int) -> tuple[str, str]:
    if score >= 90:
        return "excellent", "优秀"
    if score >= 75:
        return "good", "良好"
    if score >= 60:
        return "fair", "一般"
    if score >= 40:
        return "poor", "较差"
    return "very_poor", "很差"


def _get_level_advice(level: str) -> str:
    mapping = {
        "excellent": "睡眠状态非常好，继续保持！",
        "good": "睡眠质量不错，有小幅优化空间。",
        "fair": "睡眠尚可，建议关注以下方面。",
        "poor": "睡眠质量偏低，建议调整习惯。",
        "very_poor": "睡眠问题明显，建议尽快改善。",
    }
    return mapping[level]


def _get_dimension_advice(data: SleepScoreInput) -> list[str]:
    advice = []
    if data.sleep_latency_minutes > 45:
        advice.append("入睡耗时超过 45 分钟，建议建立固定睡前仪式。")
    if data.awakenings >= 3:
        advice.append("夜间醒来频繁，建议排查环境干扰因素。")
    if data.sleep_quality <= 2:
        advice.append("自评睡眠质量较低，建议记录具体不适感受。")
    if data.stress_level >= 8:
        advice.append("压力水平偏高，建议睡前进行放松练习。")
    if data.screen_time_minutes > 60:
        advice.append("睡前屏幕时间过长，建议提前 1 小时远离屏幕。")
    return advice


def calculate_sleep_score(data: SleepScoreInput) -> SleepScoreResult:
    latency = _score_latency(data.sleep_latency_minutes)
    awakenings = _score_awakenings(data.awakenings)
    quality = _score_quality(data.sleep_quality)
    stress = _score_stress(data.stress_level)
    screen = _score_screen(data.screen_time_minutes)

    total = latency + awakenings + quality + stress + screen
    level, level_label = _get_level(total)

    breakdown = {
        "latency": {"score": latency, "max_score": 20, "label": "入睡耗时"},
        "awakenings": {"score": awakenings, "max_score": 20, "label": "夜间醒来"},
        "quality": {"score": quality, "max_score": 25, "label": "睡眠质量"},
        "stress": {"score": stress, "max_score": 20, "label": "压力水平"},
        "screen": {"score": screen, "max_score": 15, "label": "屏幕时间"},
    }

    level_advice = _get_level_advice(level)
    dim_advice = _get_dimension_advice(data)

    advice_list = [level_advice]
    seen = {level_advice}
    for a in dim_advice:
        if a not in seen:
            advice_list.append(a)
            seen.add(a)
    advice_list = advice_list[:5]

    return SleepScoreResult(
        score=total,
        level=level,
        level_label=level_label,
        advice=advice_list,
        breakdown=breakdown,
    )
