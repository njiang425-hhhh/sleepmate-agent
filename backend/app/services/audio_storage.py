import logging
import os
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIO_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "audio"


class AudioStorage:
    def __init__(self, audio_dir: Path = AUDIO_DIR):
        self.audio_dir = audio_dir
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def build_filename(self, cache_key: str) -> str:
        return f"{cache_key}.mp3"

    def exists(self, cache_key: str) -> bool:
        path = self.audio_dir / self.build_filename(cache_key)
        return path.is_file() and path.stat().st_size > 0

    def resolve_path(self, cache_key: str) -> Path:
        return self.audio_dir / self.build_filename(cache_key)

    def create_tmp_path(self, cache_key: str) -> Path:
        return self.audio_dir / f"{cache_key}.{uuid.uuid4().hex[:8]}.part"

    def atomic_write(self, tmp_path: Path, cache_key: str) -> None:
        dest = self.resolve_path(cache_key)
        os.replace(str(tmp_path), str(dest))

    def cleanup_tmp(self, tmp_path: Path) -> None:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
