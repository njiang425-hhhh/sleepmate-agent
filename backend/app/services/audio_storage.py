import logging
import os
import time
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

    def cleanup_expired(self, retention_hours: int) -> int:
        """Remove .mp3 files older than retention_hours. Returns count deleted."""
        if retention_hours <= 0:
            return 0
        cutoff = time.time() - (retention_hours * 3600)
        deleted = 0
        for f in self.audio_dir.glob("*.mp3"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    deleted += 1
            except OSError as e:
                logger.warning("Failed to delete expired audio %s: %s", f.name, e)
        if deleted:
            logger.info("Cleaned up %d expired audio files", deleted)
        return deleted

    def enforce_max_size(self, max_total_mb: int) -> int:
        """If total .mp3 size exceeds max_total_mb, delete oldest files first.
        Never deletes .gitkeep or .part files. Returns count deleted."""
        if max_total_mb <= 0:
            return 0

        mp3_files = sorted(
            [f for f in self.audio_dir.glob("*.mp3")],
            key=lambda f: f.stat().st_mtime,
        )
        if not mp3_files:
            return 0

        total_bytes = sum(f.stat().st_size for f in mp3_files)
        max_bytes = max_total_mb * 1024 * 1024
        deleted = 0

        for f in mp3_files:
            if total_bytes <= max_bytes:
                break
            try:
                size = f.stat().st_size
                f.unlink()
                total_bytes -= size
                deleted += 1
            except OSError as e:
                logger.warning("Failed to delete oversized audio %s: %s", f.name, e)

        if deleted:
            logger.info(
                "Enforced audio size limit: deleted %d files, freed ~%.1f MB",
                deleted, (max_bytes - total_bytes) / (1024 * 1024) if total_bytes < max_bytes else 0,
            )
        return deleted

    def run_cleanup(self, retention_hours: int, max_total_mb: int) -> None:
        """Run full cleanup cycle. Called at startup. Never raises."""
        try:
            self.cleanup_expired(retention_hours)
        except Exception as e:
            logger.error("Audio expired cleanup failed: %s", e)
        try:
            self.enforce_max_size(max_total_mb)
        except Exception as e:
            logger.error("Audio size enforcement failed: %s", e)
