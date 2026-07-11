from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

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


# import model so it is registered on Base.metadata before create_all
from app.models.sleep_log import SleepLog  # noqa: E402, F401


def setup_module():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=TEST_ENGINE)


def teardown_module():
    Base.metadata.drop_all(bind=TEST_ENGINE)


def _fresh_client():
    """Each test function gets a clean DB via drop / recreate."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    return TestClient(app)


def _insert_log(client, log_date: str, **overrides) -> dict:
    payload = {
        "log_date": log_date,
        "bedtime": "23:30",
        "wake_time": "07:00",
        "sleep_latency_minutes": 15,
        "awakenings": 1,
        "sleep_quality": 4,
        "mood_before_sleep": "relaxed",
        "stress_level": 3,
        "caffeine_after_3pm": False,
        "screen_time_minutes": 30,
        "notes": None,
    }
    payload.update(overrides)
    resp = client.post("/api/v1/sleep-log", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------- Empty state ----------


def test_empty_dashboard():
    client = _fresh_client()
    resp = client.get("/api/v1/dashboard/summary?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["record_count"] == 0
    assert data["averages"] is None
    assert data["latest_score"] is None
    assert data["advice"] == ["暂无睡眠记录，请先填写睡眠日志。"]


# ---------- Single record ----------


def test_single_record():
    client = _fresh_client()
    today = date.today().isoformat()
    _insert_log(client, today, sleep_latency_minutes=20, sleep_quality=4, stress_level=3)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()

    assert data["record_count"] == 1
    assert data["averages"]["sleep_latency_minutes"] == 20.0
    assert data["averages"]["sleep_quality"] == 4.0
    assert data["averages"]["stress_level"] == 3.0
    assert data["latest_score"] is not None
    assert data["latest_score"]["date"] == today


# ---------- Multiple records averages ----------


def test_multiple_records_averages():
    client = _fresh_client()
    today = date.today()

    _insert_log(client, (today - timedelta(days=0)).isoformat(),
                sleep_latency_minutes=10, awakenings=0, sleep_quality=5,
                stress_level=2, screen_time_minutes=0)
    _insert_log(client, (today - timedelta(days=1)).isoformat(),
                sleep_latency_minutes=20, awakenings=2, sleep_quality=3,
                stress_level=6, screen_time_minutes=40)
    _insert_log(client, (today - timedelta(days=2)).isoformat(),
                sleep_latency_minutes=30, awakenings=1, sleep_quality=4,
                stress_level=4, screen_time_minutes=20)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()

    assert data["record_count"] == 3
    assert data["averages"]["sleep_latency_minutes"] == 20.0  # (10+20+30)/3
    assert data["averages"]["awakenings"] == 1.0  # (0+2+1)/3
    assert data["averages"]["sleep_quality"] == 4.0  # (5+3+4)/3
    assert data["averages"]["stress_level"] == 4.0  # (2+6+4)/3
    assert data["averages"]["screen_time_minutes"] == 20.0  # (0+40+20)/3
    assert isinstance(data["averages"]["score"], float)


# ---------- latest_score by log_date ----------


def test_latest_score_by_log_date():
    client = _fresh_client()
    today = date.today()

    _insert_log(client, (today - timedelta(days=2)).isoformat(), sleep_quality=3)
    _insert_log(client, today.isoformat(), sleep_quality=5)
    _insert_log(client, (today - timedelta(days=1)).isoformat(), sleep_quality=4)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()

    assert data["latest_score"]["date"] == today.isoformat()


# ---------- latest_score contains breakdown ----------


def test_latest_score_breakdown():
    client = _fresh_client()
    today = date.today().isoformat()
    _insert_log(client, today)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()

    ls = data["latest_score"]
    assert "breakdown" in ls
    bk = ls["breakdown"]
    assert set(bk.keys()) == {"latency", "awakenings", "quality", "stress", "screen"}
    for key, item in bk.items():
        assert "score" in item
        assert "max_score" in item
        assert "label" in item


# ---------- days boundaries ----------


def test_days_default():
    client = _fresh_client()
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    assert resp.json()["days"] == 7


def test_days_1():
    client = _fresh_client()
    today = date.today().isoformat()
    _insert_log(client, today)
    _insert_log(client, (date.today() - timedelta(days=1)).isoformat())

    resp = client.get("/api/v1/dashboard/summary?days=1")
    data = resp.json()
    assert data["record_count"] == 1


def test_days_30():
    client = _fresh_client()
    _insert_log(client, (date.today() - timedelta(days=29)).isoformat())
    resp = client.get("/api/v1/dashboard/summary?days=30")
    assert resp.status_code == 200
    assert resp.json()["record_count"] == 1


def test_days_too_low():
    client = _fresh_client()
    resp = client.get("/api/v1/dashboard/summary?days=0")
    assert resp.status_code == 422


def test_days_too_high():
    client = _fresh_client()
    resp = client.get("/api/v1/dashboard/summary?days=31")
    assert resp.status_code == 422


# ---------- Exclude future dates ----------


def test_exclude_future_dates():
    client = _fresh_client()
    future = (date.today() + timedelta(days=3)).isoformat()
    _insert_log(client, future)

    resp = client.get("/api/v1/dashboard/summary?days=30")
    data = resp.json()
    assert data["record_count"] == 0


# ---------- Average decimal precision ----------


def test_average_decimal_precision():
    client = _fresh_client()
    today = date.today()

    _insert_log(client, today.isoformat(), sleep_quality=3)
    _insert_log(client, (today - timedelta(days=1)).isoformat(), sleep_quality=4)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()
    assert data["averages"]["sleep_quality"] == 3.5


# ---------- Score dynamic calculation ----------


def test_score_dynamic_calculation():
    client = _fresh_client()
    today = date.today()

    _insert_log(client, today.isoformat(),
                sleep_latency_minutes=5, awakenings=0, sleep_quality=5,
                stress_level=1, screen_time_minutes=0)
    _insert_log(client, (today - timedelta(days=1)).isoformat(),
                sleep_latency_minutes=90, awakenings=6, sleep_quality=1,
                stress_level=10, screen_time_minutes=120)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()
    avg_score = data["averages"]["score"]
    assert avg_score == 50.0  # (100 + 0) / 2


# ---------- Advice dedup and max 5 ----------


def test_advice_dedup_and_limit():
    client = _fresh_client()
    today = date.today()

    _insert_log(client, today.isoformat(),
                sleep_latency_minutes=50, awakenings=3, sleep_quality=2,
                stress_level=9, screen_time_minutes=80)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()

    advice = data["advice"]
    assert len(advice) == len(set(advice))
    assert len(advice) <= 5


def test_advice_merges_trend_and_latest():
    client = _fresh_client()
    today = date.today().isoformat()
    _insert_log(client, today, sleep_latency_minutes=50)

    resp = client.get("/api/v1/dashboard/summary?days=7")
    data = resp.json()
    assert any("入睡耗时超过 45 分钟" in a for a in data["advice"])
