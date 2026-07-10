from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "mood": "relaxed",
    "energy_level": 5,
    "stress_level": 4,
    "caffeine_after_3pm": False,
    "screen_time_minutes": 30,
    "available_minutes": 15,
    "preferred_audio": "rain",
}


def test_checkin_valid_request_returns_200():
    response = client.post("/api/v1/checkin", json=VALID_PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "checkin" in data
    assert "analysis" in data
    assert "sleep_risk_level" in data["analysis"]
    assert "suggestions" in data["analysis"]
    assert "recommended_activity" in data["analysis"]
    assert "recommended_duration_minutes" in data["analysis"]


def test_checkin_stress_level_out_of_range():
    payload = {**VALID_PAYLOAD, "stress_level": 11}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422

    payload = {**VALID_PAYLOAD, "stress_level": 0}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422


def test_checkin_screen_time_negative():
    payload = {**VALID_PAYLOAD, "screen_time_minutes": -1}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422


def test_checkin_available_minutes_invalid():
    payload = {**VALID_PAYLOAD, "available_minutes": 7}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422


def test_checkin_mood_invalid():
    payload = {**VALID_PAYLOAD, "mood": "happy"}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422


def test_checkin_preferred_audio_invalid():
    payload = {**VALID_PAYLOAD, "preferred_audio": "guitar"}
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 422


def test_checkin_high_risk_returns_suggestions():
    payload = {
        "mood": "stressed",
        "energy_level": 9,
        "stress_level": 9,
        "caffeine_after_3pm": True,
        "screen_time_minutes": 150,
        "available_minutes": 10,
        "preferred_audio": "none",
    }
    response = client.post("/api/v1/checkin", json=payload)
    assert response.status_code == 200
    data = response.json()
    analysis = data["analysis"]
    assert analysis["sleep_risk_level"] == "high"
    assert len(analysis["suggestions"]) >= 3
    combined = " ".join(analysis["suggestions"])
    assert "咖啡因" in combined or "屏幕" in combined or "压力" in combined
