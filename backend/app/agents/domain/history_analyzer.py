from app.models.sleep_log import SleepLog


def analyze_history(logs: list[SleepLog]) -> dict:
    record_count = len(logs)
    if record_count == 0:
        return {
            "history_available": False,
            "record_count": 0,
            "avg_latency": None,
            "avg_awakenings": None,
            "avg_quality": None,
            "avg_stress": None,
            "avg_screen": None,
        }

    return {
        "history_available": True,
        "record_count": record_count,
        "avg_latency": round(
            sum(l.sleep_latency_minutes for l in logs) / record_count, 1
        ),
        "avg_awakenings": round(
            sum(l.awakenings for l in logs) / record_count, 1
        ),
        "avg_quality": round(
            sum(l.sleep_quality for l in logs) / record_count, 1
        ),
        "avg_stress": round(
            sum(l.stress_level for l in logs) / record_count, 1
        ),
        "avg_screen": round(
            sum(l.screen_time_minutes for l in logs) / record_count, 1
        ),
    }
