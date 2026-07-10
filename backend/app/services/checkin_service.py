from app.schemas.checkin import AnalysisResult, CheckinRequest


def analyze_checkin(request: CheckinRequest) -> AnalysisResult:
    score = 0
    triggers: list[str] = []

    if request.stress_level >= 7:
        score += 2
        triggers.append("high_stress")

    if request.energy_level >= 8:
        score += 1
        triggers.append("high_energy")

    if request.caffeine_after_3pm:
        score += 2
        triggers.append("caffeine")

    if request.screen_time_minutes > 120:
        score += 3
        triggers.append("very_high_screen_time")
    elif request.screen_time_minutes > 60:
        score += 2
        triggers.append("high_screen_time")

    if request.mood in ("anxious", "stressed"):
        score += 1
        triggers.append("negative_mood")

    if request.available_minutes == 5:
        score += 1
        triggers.append("limited_time")

    if score <= 2:
        risk_level = "low"
    elif score <= 5:
        risk_level = "medium"
    else:
        risk_level = "high"

    suggestions: list[str] = []
    if "caffeine" in triggers:
        suggestions.append("咖啡因摄入可能影响入睡，建议避免在睡前摄入咖啡因")
    if "high_screen_time" in triggers:
        suggestions.append("屏幕时间较长，建议减少蓝光暴露以促进褪黑素分泌")
    if "very_high_screen_time" in triggers:
        suggestions.append("屏幕时间过长，强烈建议立即放下手机进行放松活动")
    if "high_stress" in triggers:
        suggestions.append("压力水平较高，建议进行深呼吸或冥想放松")
    if "negative_mood" in triggers:
        suggestions.append("情绪状态不佳，建议尝试渐进式肌肉放松")
    if "high_energy" in triggers:
        suggestions.append("精力充沛，建议通过轻度拉伸消耗多余能量")
    if "limited_time" in triggers:
        suggestions.append("可用时间较短，建议选择快速放松技巧")
    if not suggestions:
        suggestions.append("状态良好，建议保持当前放松节奏")

    activity_map = {
        "high_stress": "breathing_exercise",
        "negative_mood": "meditation",
        "very_high_screen_time": "breathing_exercise",
        "high_screen_time": "stretching",
        "high_energy": "stretching",
        "limited_time": "breathing_exercise",
        "caffeine": "audio_relaxation",
    }
    recommended_activity = "meditation"
    for trigger in triggers:
        if trigger in activity_map:
            recommended_activity = activity_map[trigger]
            break

    duration_map = {
        "breathing_exercise": 5,
        "meditation": 10,
        "stretching": 10,
        "audio_relaxation": 15,
    }
    recommended_duration = min(
        duration_map.get(recommended_activity, 10),
        request.available_minutes,
    )

    return AnalysisResult(
        sleep_risk_level=risk_level,
        suggestions=suggestions,
        recommended_activity=recommended_activity,
        recommended_duration_minutes=recommended_duration,
    )
