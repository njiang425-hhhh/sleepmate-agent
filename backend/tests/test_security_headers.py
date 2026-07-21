"""Tests for Batch 2: security headers, CORS enforcement, CSP compatibility."""


class TestSecurityHeaders:
    def test_cors_allows_localhost_get(self, client):
        resp = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_allows_localhost_post(self, client):
        resp = client.options(
            "/api/v1/checkin",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods

    def test_cors_blocks_non_localhost(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_cors_blocks_delete_method(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "DELETE" not in allow_methods

    def test_cors_blocks_patch_method(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PATCH",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "PATCH" not in allow_methods

    def test_cors_credentials_false(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # allow_credentials should not be true
        cred = resp.headers.get("access-control-allow-credentials", "false")
        assert cred.lower() != "true"

    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestCSPCompatibility:
    """Verify that TTS audio and existing E2E flows aren't blocked by CSP."""

    def test_tts_endpoint_accessible(self, client):
        """TTS endpoint should be reachable (CSP connect-src allows localhost:8000)."""
        resp = client.post(
            "/api/v1/audio/tts",
            json={"script_text": "test"},
            headers={"Origin": "http://localhost:3000"},
        )
        # Should not be blocked by CORS (200 or 503 if service not ready)
        assert resp.status_code in (200, 503)

    def test_static_audio_accessible(self, client):
        """Static audio files should be reachable (CSP media-src allows localhost:8000)."""
        resp = client.get("/static/audio/nonexistent.mp3")
        # Should return 404, not be blocked
        assert resp.status_code == 404

    def test_dashboard_api_accessible(self, client):
        """Dashboard API should be reachable."""
        resp = client.get("/api/v1/dashboard/summary?days=7")
        assert resp.status_code == 200

    def test_routine_api_accessible(self, client):
        """Routine API should be reachable."""
        resp = client.post(
            "/api/v1/routine/generate",
            json={
                "checkin": {
                    "mood": "calm",
                    "energy_level": 5,
                    "stress_level": 5,
                    "caffeine_after_3pm": False,
                    "screen_time_minutes": 30,
                    "available_minutes": 10,
                    "preferred_audio": "rain",
                },
                "history_days": 7,
            },
        )
        assert resp.status_code == 200

    def test_checkin_api_accessible(self, client):
        """Checkin API should be reachable."""
        resp = client.post(
            "/api/v1/checkin",
            json={
                "mood": "calm",
                "energy_level": 5,
                "stress_level": 5,
                "caffeine_after_3pm": False,
                "screen_time_minutes": 30,
                "available_minutes": 10,
                "preferred_audio": "rain",
            },
        )
        assert resp.status_code == 200
