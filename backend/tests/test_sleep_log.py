from datetime import date, time
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


# ---------- fixtures ----------

VALID_PAYLOAD = {
    "log_date": "2026-07-10",
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


def _fresh_client():
    """Each test function gets a clean DB via begin / rollback."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    return TestClient(app)


# ---------- tests: POST /api/v1/sleep-log ----------


def test_create_sleep_log_valid():
    client = _fresh_client()
    response = client.post("/api/v1/sleep-log", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["log_date"] == "2026-07-10"
    assert data["sleep_quality"] == 4
    assert data["stress_level"] == 3
    assert "id" in data
    assert "created_at" in data


def test_create_sleep_log_duplicate_date():
    client = _fresh_client()
    resp1 = client.post("/api/v1/sleep-log", json=VALID_PAYLOAD)
    assert resp1.status_code == 201
    resp2 = client.post("/api/v1/sleep-log", json=VALID_PAYLOAD)
    assert resp2.status_code == 409


def test_create_sleep_log_quality_out_of_range():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "sleep_quality": 6}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_quality_zero():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "sleep_quality": 0}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_invalid_time():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "bedtime": "25:99"}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_invalid_wake_time():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "wake_time": "99:99"}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_stress_out_of_range():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "stress_level": 0}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_stress_too_high():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "stress_level": 11}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_negative_latency():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "sleep_latency_minutes": -1}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


def test_create_sleep_log_negative_awakenings():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "awakenings": -1}
    response = client.post("/api/v1/sleep-log", json=payload)
    assert response.status_code == 422


# ---------- tests: GET /api/v1/sleep-log/recent ----------


def test_get_recent_7_days():
    client = _fresh_client()
    today = date.today()
    for i in range(10):
        d = today - __import__("datetime").timedelta(days=9 - i)
        payload = {**VALID_PAYLOAD, "log_date": d.isoformat()}
        resp = client.post("/api/v1/sleep-log", json=payload)
        assert resp.status_code == 201

    response = client.get("/api/v1/sleep-log/recent?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 7
    dates = [log["log_date"] for log in data["logs"]]
    assert dates == sorted(dates, reverse=True)


def test_get_recent_1_day():
    client = _fresh_client()
    payload = {**VALID_PAYLOAD, "log_date": date.today().isoformat()}
    resp = client.post("/api/v1/sleep-log", json=payload)
    assert resp.status_code == 201

    response = client.get("/api/v1/sleep-log/recent?days=1")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_get_recent_days_too_low():
    client = _fresh_client()
    response = client.get("/api/v1/sleep-log/recent?days=0")
    assert response.status_code == 422


def test_get_recent_days_too_high():
    client = _fresh_client()
    response = client.get("/api/v1/sleep-log/recent?days=31")
    assert response.status_code == 422


def test_get_recent_empty():
    client = _fresh_client()
    response = client.get("/api/v1/sleep-log/recent?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["logs"] == []


# ---------- test: DB isolation ----------


def test_db_isolation():
    client1 = _fresh_client()
    payload = {**VALID_PAYLOAD, "log_date": "2026-06-01"}
    resp = client1.post("/api/v1/sleep-log", json=payload)
    assert resp.status_code == 201

    client2 = _fresh_client()
    response = client2.get("/api/v1/sleep-log/recent?days=30")
    data = response.json()
    assert data["count"] == 0
