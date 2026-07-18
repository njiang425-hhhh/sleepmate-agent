import asyncio
import hashlib
import logging
from dataclasses import dataclass

from app.services.audio_storage import AudioStorage
from app.services.tts_provider import TTSProvider

logger = logging.getLogger(__name__)


class TTSConfigurationError(Exception):
    pass


class TTSUnavailableError(Exception):
    pass


class TTSStorageError(Exception):
    pass


@dataclass(frozen=True)
class TTSConfig:
    model: str
    voice: str
    speed: float
    response_format: str
    instructions: str
    provider_name: str
    max_chars: int


class TTSService:
    def __init__(self, provider: TTSProvider, storage: AudioStorage, config: TTSConfig):
        self._provider = provider
        self._storage = storage
        self._config = config
        self._locks: dict[str, asyncio.Lock] = {}

    def _build_cache_key(self, text: str) -> str:
        normalized = " ".join(text.strip().split())
        payload = "|".join([
            normalized,
            self._config.provider_name,
            self._config.model,
            self._config.voice,
            self._config.instructions,
            str(self._config.speed),
            self._config.response_format,
        ])
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def _get_lock(self, cache_key: str) -> asyncio.Lock:
        if cache_key not in self._locks:
            self._locks[cache_key] = asyncio.Lock()
        return self._locks[cache_key]

    async def generate(self, text: str) -> tuple[str, bool]:
        cache_key = self._build_cache_key(text)

        if self._storage.exists(cache_key):
            return f"/static/audio/{self._storage.build_filename(cache_key)}", True

        lock = self._get_lock(cache_key)
        async with lock:
            if self._storage.exists(cache_key):
                return f"/static/audio/{self._storage.build_filename(cache_key)}", True

            tmp_path = self._storage.create_tmp_path(cache_key)
            try:
                await self._provider.synthesize(
                    text.strip(),
                    self._config.instructions,
                    tmp_path,
                )
                if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                    raise TTSStorageError("TTS provider produced empty output")
                self._storage.atomic_write(tmp_path, cache_key)
                return f"/static/audio/{self._storage.build_filename(cache_key)}", False
            except (TTSStorageError, TTSConfigurationError, TTSUnavailableError):
                self._storage.cleanup_tmp(tmp_path)
                raise
            except OSError as e:
                self._storage.cleanup_tmp(tmp_path)
                logger.error("TTS storage error: %s", e)
                raise TTSStorageError("Storage error") from e
            except Exception as e:
                self._storage.cleanup_tmp(tmp_path)
                logger.error("TTS synthesis failed: %s", e)
                raise TTSUnavailableError("TTS service unavailable") from e
