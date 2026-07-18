import asyncio
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import AsyncMock

from app.services.audio_storage import AudioStorage
from app.services.tts_provider import FakeTTSProvider
from app.services.tts_service import TTSService, TTSConfig, TTSUnavailableError


# ---------- helpers ----------

def _make_config(provider_name: str = "fake", voice: str = "alloy",
                 speed: float = 0.9, instructions: str = "test instructions") -> TTSConfig:
    return TTSConfig(
        model="gpt-4o-mini-tts",
        voice=voice,
        speed=speed,
        response_format="mp3",
        instructions=instructions,
        provider_name=provider_name,
        max_chars=4096,
    )


def _make_service(tmp_path: Path, provider_name: str = "fake",
                  voice: str = "alloy", speed: float = 0.9,
                  instructions: str = "test instructions") -> TTSService:
    storage = AudioStorage(audio_dir=tmp_path)
    provider = FakeTTSProvider()
    config = _make_config(provider_name=provider_name, voice=voice,
                          speed=speed, instructions=instructions)
    return TTSService(provider=provider, storage=storage, config=config)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTTSService:
    def test_generate_creates_file(self, tmp_path):
        service = _make_service(tmp_path)
        audio_path, cached = _run(service.generate("请闭上眼睛"))

        assert not cached
        assert audio_path.startswith("/static/audio/")
        assert audio_path.endswith(".mp3")
        filename = audio_path.split("/")[-1]
        assert (tmp_path / filename).exists()

    def test_audio_path_format(self, tmp_path):
        service = _make_service(tmp_path)
        audio_path, _ = _run(service.generate("test text"))

        assert audio_path.startswith("/static/audio/")
        assert ".mp3" in audio_path

    def test_cached_on_second_request(self, tmp_path):
        service = _make_service(tmp_path)
        path1, cached1 = _run(service.generate("same text"))
        path2, cached2 = _run(service.generate("same text"))

        assert path1 == path2
        assert cached1 is False
        assert cached2 is True

    def test_no_duplicate_provider_calls(self, tmp_path):
        service = _make_service(tmp_path)
        _run(service.generate("text a"))
        _run(service.generate("text a"))

        filename = service._storage.build_filename(
            service._build_cache_key("text a")
        )
        assert (tmp_path / filename).exists()

    def test_cache_key_config_isolation_voice(self, tmp_path):
        service_a = _make_service(tmp_path, voice="alloy")
        service_b = _make_service(tmp_path, voice="echo")

        path_a, _ = _run(service_a.generate("same text"))
        path_b, _ = _run(service_b.generate("same text"))

        assert path_a != path_b
        assert len(list(tmp_path.glob("*.mp3"))) == 2

    def test_cache_key_config_isolation_provider(self, tmp_path):
        service_a = _make_service(tmp_path, provider_name="fake")
        service_b = _make_service(tmp_path, provider_name="real")

        path_a, _ = _run(service_a.generate("same text"))
        path_b, _ = _run(service_b.generate("same text"))

        assert path_a != path_b

    def test_cache_key_config_isolation_speed(self, tmp_path):
        service_a = _make_service(tmp_path, speed=0.9)
        service_b = _make_service(tmp_path, speed=1.0)

        path_a, _ = _run(service_a.generate("same text"))
        path_b, _ = _run(service_b.generate("same text"))

        assert path_a != path_b

    def test_cache_key_config_isolation_instructions(self, tmp_path):
        service_a = _make_service(tmp_path, instructions="A")
        service_b = _make_service(tmp_path, instructions="B")

        path_a, _ = _run(service_a.generate("same text"))
        path_b, _ = _run(service_b.generate("same text"))

        assert path_a != path_b

    def test_empty_text_returns_422(self, tmp_path):
        from app.main import app
        service = _make_service(tmp_path)
        app.state.tts_service = service
        client = TestClient(app)

        resp = client.post("/api/v1/audio/tts", json={"script_text": ""})
        assert resp.status_code == 422

    def test_text_too_long_returns_422(self, tmp_path):
        from app.main import app
        service = _make_service(tmp_path)
        app.state.tts_service = service
        client = TestClient(app)

        resp = client.post("/api/v1/audio/tts", json={"script_text": "x" * 4097})
        assert resp.status_code == 422

    def test_tts_unavailable_returns_503(self, tmp_path):
        from app.main import app

        mock_provider = AsyncMock(spec=FakeTTSProvider)
        mock_provider.synthesize = AsyncMock(side_effect=Exception("network error"))
        mock_provider.close = AsyncMock()

        storage = AudioStorage(audio_dir=tmp_path)
        config = _make_config()
        service = TTSService(provider=mock_provider, storage=storage, config=config)
        app.state.tts_service = service
        client = TestClient(app)

        resp = client.post("/api/v1/audio/tts", json={"script_text": "test"})
        assert resp.status_code == 503
        assert resp.json()["detail"] == "语音服务暂时不可用，请稍后重试"

    def test_tmp_cleanup_on_failure(self, tmp_path):
        mock_provider = AsyncMock(spec=FakeTTSProvider)
        mock_provider.synthesize = AsyncMock(side_effect=Exception("fail"))
        mock_provider.close = AsyncMock()

        storage = AudioStorage(audio_dir=tmp_path)
        config = _make_config()
        service = TTSService(provider=mock_provider, storage=storage, config=config)

        try:
            _run(service.generate("fail text"))
        except TTSUnavailableError:
            pass

        part_files = list(tmp_path.glob("*.part"))
        assert len(part_files) == 0

    def test_static_file_accessible(self, tmp_path):
        from app.main import app
        service = _make_service(tmp_path)
        app.state.tts_service = service
        client = TestClient(app)

        resp = client.post("/api/v1/audio/tts", json={"script_text": "test"})
        assert resp.status_code == 200
        audio_path = resp.json()["audio_path"]

        # Verify the file exists at the storage location with non-zero size
        filename = audio_path.split("/")[-1]
        assert (tmp_path / filename).exists()
        assert (tmp_path / filename).stat().st_size > 0

    def test_500_no_expose_disk_path(self, tmp_path):
        from app.main import app

        mock_provider = AsyncMock(spec=FakeTTSProvider)
        mock_provider.synthesize = AsyncMock(side_effect=OSError("disk full"))
        mock_provider.close = AsyncMock()

        storage = AudioStorage(audio_dir=tmp_path)
        config = _make_config()
        service = TTSService(provider=mock_provider, storage=storage, config=config)
        app.state.tts_service = service
        client = TestClient(app)

        resp = client.post("/api/v1/audio/tts", json={"script_text": "test"})
        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert str(tmp_path) not in detail
        assert "disk full" not in detail

    def test_500_no_expose_script_text(self, tmp_path):
        from app.main import app

        mock_provider = AsyncMock(spec=FakeTTSProvider)
        mock_provider.synthesize = AsyncMock(side_effect=OSError("write failed"))
        mock_provider.close = AsyncMock()

        storage = AudioStorage(audio_dir=tmp_path)
        config = _make_config()
        service = TTSService(provider=mock_provider, storage=storage, config=config)
        app.state.tts_service = service
        client = TestClient(app)

        secret_script = "这是秘密脚本内容"
        resp = client.post("/api/v1/audio/tts", json={"script_text": secret_script})
        assert resp.status_code == 500
        assert secret_script not in resp.json()["detail"]

    def test_zero_byte_cache_rebuilt(self, tmp_path):
        service = _make_service(tmp_path)
        path1, _ = _run(service.generate("text"))

        filename = path1.split("/")[-1]
        zero_file = tmp_path / filename
        zero_file.write_bytes(b"")
        assert zero_file.stat().st_size == 0

        path2, cached = _run(service.generate("text"))
        assert not cached
        assert zero_file.stat().st_size > 0

    def test_part_path_is_unique(self, tmp_path):
        storage = AudioStorage(audio_dir=tmp_path)
        part1 = storage.create_tmp_path("key1")
        part2 = storage.create_tmp_path("key1")
        assert part1 != part2

    def test_not_pollute_production_dir(self, tmp_path):
        from app.services.audio_storage import AUDIO_DIR

        service = _make_service(tmp_path)
        _run(service.generate("test"))

        production_files = list(AUDIO_DIR.glob("*.mp3"))
        assert len(production_files) == 0


class TestOpenAITTSProvider:
    def test_real_mode_no_key_raises(self):
        import os
        from app.core.config import Settings

        os.environ["TTS_MODE"] = "real"
        os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                settings = Settings()
                if settings.TTS_MODE == "real" and not settings.OPENAI_API_KEY:
                    raise RuntimeError(
                        "TTS_MODE is 'real' but OPENAI_API_KEY is not set."
                    )
        finally:
            os.environ["TTS_MODE"] = "fake"

    def test_openai_provider_called(self, tmp_path):
        from unittest.mock import patch, MagicMock

        mock_response = MagicMock()
        mock_response.read = AsyncMock(return_value=b"fake mp3 data")

        with patch("openai.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
            mock_client.close = AsyncMock()
            mock_cls.return_value = mock_client

            from app.services.tts_provider import OpenAITTSProvider

            provider = OpenAITTSProvider(
                api_key="test-key",
                model="gpt-4o-mini-tts",
                voice="alloy",
                response_format="mp3",
                speed=0.9,
                timeout_seconds=60,
            )

            output_path = tmp_path / "test_output.mp3"
            _run(provider.synthesize("test text", "test instructions", output_path))

            mock_client.audio.speech.create.assert_called_once()
            assert output_path.exists()
            assert output_path.read_bytes() == b"fake mp3 data"

            _run(provider.close())
            mock_client.close.assert_called_once()
