from sqlalchemy.orm import Session

from app.repositories import sleep_log_repo
from app.schemas.dashboard import (
    DashboardAverages,
    DashboardSummaryResponse,
    LatestScoreItem,
    ScoreBreakdownItem,
)
from app.services.sleep_score_service import SleepScoreInput, calculate_sleep_score


def get_dashboard_summary(db: Session, days: int) -> DashboardSummaryResponse:
    logs = sleep_log_repo.get_logs_for_dashboard(db, days)
    count = len(logs)

    if count == 0:
        return DashboardSummaryResponse(
            days=days,
            record_count=0,
            averages=None,
            latest_score=None,
            advice=["暂无睡眠记录，请先填写睡眠日志。"],
        )

    total_latency = sum(l.sleep_latency_minutes for l in logs)
    total_awakenings = sum(l.awakenings for l in logs)
    total_quality = sum(l.sleep_quality for l in logs)
    total_stress = sum(l.stress_level for l in logs)
    total_screen = sum(l.screen_time_minutes for l in logs)

    scores = []
    for l in logs:
        inp = SleepScoreInput(
            sleep_latency_minutes=l.sleep_latency_minutes,
            awakenings=l.awakenings,
            sleep_quality=l.sleep_quality,
            stress_level=l.stress_level,
            screen_time_minutes=l.screen_time_minutes,
        )
        scores.append(calculate_sleep_score(inp).score)

    avg_latency = round(total_latency / count, 1)
    avg_awakenings = round(total_awakenings / count, 1)
    avg_quality = round(total_quality / count, 1)
    avg_stress = round(total_stress / count, 1)
    avg_screen = round(total_screen / count, 1)
    avg_score = round(sum(scores) / count, 1)

    averages = DashboardAverages(
        sleep_latency_minutes=avg_latency,
        awakenings=avg_awakenings,
        sleep_quality=avg_quality,
        stress_level=avg_stress,
        screen_time_minutes=avg_screen,
        score=avg_score,
    )

    latest = logs[0]
    latest_input = SleepScoreInput(
        sleep_latency_minutes=latest.sleep_latency_minutes,
        awakenings=latest.awakenings,
        sleep_quality=latest.sleep_quality,
        stress_level=latest.stress_level,
        screen_time_minutes=latest.screen_time_minutes,
    )
    latest_result = calculate_sleep_score(latest_input)

    latest_breakdown = {
        k: ScoreBreakdownItem(score=v["score"], max_score=v["max_score"], label=v["label"])
        for k, v in latest_result.breakdown.items()
    }

    latest_score = LatestScoreItem(
        date=str(latest.log_date),
        score=latest_result.score,
        level=latest_result.level,
        level_label=latest_result.level_label,
        breakdown=latest_breakdown,
    )

    trend_input = SleepScoreInput(
        sleep_latency_minutes=int(avg_latency),
        awakenings=int(round(avg_awakenings)),
        sleep_quality=int(round(avg_quality)),
        stress_level=int(round(avg_stress)),
        screen_time_minutes=int(avg_screen),
    )
    trend_result = calculate_sleep_score(trend_input)

    advice_set: list[str] = []
    seen: set[str] = set()

    for a in latest_result.advice:
        if a not in seen:
            advice_set.append(a)
            seen.add(a)

    for a in trend_result.advice:
        if a not in seen:
            advice_set.append(a)
            seen.add(a)

    advice_set = advice_set[:5]

    return DashboardSummaryResponse(
        days=days,
        record_count=count,
        averages=averages,
        latest_score=latest_score,
        advice=advice_set,
    )
