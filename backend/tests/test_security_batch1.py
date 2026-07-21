"""Tests for Batch 1 security improvements: rate limiting, audio cleanup,
notes max_length, exception handling, CORS."""

import os
import time
from unittest.mock import patch, MagicMock

from app.services.audio_storage import AudioStorage
from app.services import routine_service
from app.services.llm_provider import ProviderTimeoutError


# ── Audio Cache Cleanup ──


class TestAudioCleanup:
    def test_cleanup_expired_removes_old_files(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)

        old_file = tmp_path / "old_audio.mp3"
        old_file.write_bytes(b"fake audio")
        old_time = time.time() - 86400 * 8
        os.utime(str(old_file), (old_time, old_time))

        recent_file = tmp_path / "recent_audio.mp3"
        recent_file.write_bytes(b"fake audio")

        deleted = storage.cleanup_expired(retention_hours=168)
        assert deleted == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_skips_gitkeep(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        gitkeep = tmp_path / ".gitkeep"
        gitkeep.write_text("")
        old_time = time.time() - 86400 * 30
        os.utime(str(gitkeep), (old_time, old_time))

        deleted = storage.cleanup_expired(retention_hours=1)
        assert deleted == 0
        assert gitkeep.exists()

    def test_cleanup_skips_part_files(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        part_file = tmp_path / "test.abc123.part"
        part_file.write_bytes(b"partial")
        old_time = time.time() - 86400 * 30
        os.utime(str(part_file), (old_time, old_time))

        deleted = storage.cleanup_expired(retention_hours=1)
        assert deleted == 0
        assert part_file.exists()

    def test_enforce_max_size_disabled_when_zero(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        f = tmp_path / "audio.mp3"
        f.write_bytes(b"x" * 200_000)

        deleted = storage.enforce_max_size(max_total_mb=0)
        assert deleted == 0
        assert f.exists()

    def test_enforce_max_size_within_limit(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        f = tmp_path / "audio.mp3"
        f.write_bytes(b"x" * 1000)

        deleted = storage.enforce_max_size(max_total_mb=1)
        assert deleted == 0
        assert f.exists()

    def test_cleanup_failure_does_not_crash(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        with patch.object(storage, "cleanup_expired", side_effect=OSError("disk error")):
            storage.run_cleanup(retention_hours=168, max_total_mb=500)


# ── SleepLogCreate.notes max_length ──


class TestNotesMaxLength:
    def test_notes_at_limit_accepted(self, client):
        payload = {
            "log_date": "2026-07-20",
            "bedtime": "23:00",
            "wake_time": "07:00",
            "sleep_latency_minutes": 15,
            "awakenings": 1,
            "sleep_quality": 4,
            "mood_before_sleep": "calm",
            "stress_level": 3,
            "caffeine_after_3pm": False,
            "screen_time_minutes": 30,
            "notes": "x" * 1000,
        }
        resp = client.post("/api/v1/sleep-log", json=payload)
        assert resp.status_code == 201

    def test_notes_over_limit_rejected(self, client):
        payload = {
            "log_date": "2026-07-21",
            "bedtime": "23:00",
            "wake_time": "07:00",
            "sleep_latency_minutes": 15,
            "awakenings": 1,
            "sleep_quality": 4,
            "mood_before_sleep": "calm",
            "stress_level": 3,
            "caffeine_after_3pm": False,
            "screen_time_minutes": 30,
            "notes": "x" * 1001,
        }
        resp = client.post("/api/v1/sleep-log", json=payload)
        assert resp.status_code == 422

    def test_notes_none_accepted(self, client):
        payload = {
            "log_date": "2026-07-22",
            "bedtime": "23:00",
            "wake_time": "07:00",
            "sleep_latency_minutes": 15,
            "awakenings": 1,
            "sleep_quality": 4,
            "mood_before_sleep": "calm",
            "stress_level": 3,
            "caffeine_after_3pm": False,
            "screen_time_minutes": 30,
            "notes": None,
        }
        resp = client.post("/api/v1/sleep-log", json=payload)
        assert resp.status_code == 201


# ── Exception Handling ──


class TestExceptionHandling:
    def test_provider_timeout_returns_503(self, client):
        with patch.object(routine_service, "get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate = MagicMock(side_effect=ProviderTimeoutError("timeout"))
            mock_get.return_value = mock_provider
            resp = client.post(
                "/api/v1/routine/generate",
                json={"checkin": {"mood": "calm", "energy_level": 5, "stress_level": 5,
                       "caffeine_after_3pm": False, "screen_time_minutes": 30,
                       "available_minutes": 10, "preferred_audio": "rain"},
                       "history_days": 7},
            )
            assert resp.status_code == 503

    def test_unknown_exception_returns_500_generic(self, client):
        with patch.object(routine_service, "get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate = MagicMock(side_effect=RuntimeError("DB connection lost"))
            mock_get.return_value = mock_provider
            resp = client.post(
                "/api/v1/routine/generate",
                json={"checkin": {"mood": "calm", "energy_level": 5, "stress_level": 5,
                       "caffeine_after_3pm": False, "screen_time_minutes": 30,
                       "available_minutes": 10, "preferred_audio": "rain"},
                       "history_days": 7},
            )
            assert resp.status_code == 500
            assert resp.json()["detail"] == "服务器内部错误"
            assert "DB connection" not in resp.json()["detail"]


# ── CORS ──


class TestCORS:
    def test_cors_allows_localhost(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    def test_cors_blocks_other_origin(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_cors_methods_restricted(self, client):
        resp = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE",
            },
        )
        allow_methods = resp.headers.get("access-control-allow-methods", "")
        assert "DELETE" not in allow_methods
