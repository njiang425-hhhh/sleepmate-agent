import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.audio import router as audio_router
from app.api.checkin import router as checkin_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.routine import router as routine_router
from app.api.sleep_log import router as sleep_log_router
from app.core.config import settings
from app.core.database import engine, Base
from app.models.sleep_log import SleepLog  # noqa: F401 — ensure model is registered

logger = logging.getLogger(__name__)

_rag_service = None


def get_rag_service():
    return _rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rag_service
    Base.metadata.create_all(bind=engine)

    if settings.RAG_ENABLED:
        try:
            from app.services.embedding_service import create_embedding_provider
            from app.services.rag_service import RAGService

            provider = create_embedding_provider()
            persist_dir = str(
                Path(__file__).resolve().parent.parent / settings.CHROMA_PERSIST_DIR
            )
            _rag_service = RAGService(
                persist_dir=persist_dir,
                collection_name=settings.CHROMA_COLLECTION_NAME,
                embedding_provider=provider,
                top_k=settings.RAG_TOP_K,
                max_context_tokens=settings.RAG_MAX_CONTEXT_TOKENS,
                max_distance=settings.RAG_MAX_DISTANCE,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            logger.info("RAG service initialized (available=%s)", _rag_service.is_available())
        except Exception as e:
            logger.error("Failed to initialize RAG service: %s", e)
            _rag_service = None
    else:
        logger.info("RAG disabled (RAG_ENABLED=False)")

    # TTS init
    from app.services.audio_storage import AudioStorage
    from app.services.tts_provider import FakeTTSProvider, OpenAITTSProvider
    from app.services.tts_service import TTSConfig, TTSService

    tts_config = TTSConfig(
        model=settings.TTS_MODEL,
        voice=settings.TTS_VOICE,
        speed=settings.TTS_SPEED,
        response_format=settings.TTS_RESPONSE_FORMAT,
        instructions=settings.TTS_INSTRUCTIONS,
        provider_name=settings.TTS_MODE,
        max_chars=settings.TTS_MAX_CHARS,
    )

    if settings.TTS_MODE == "real":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "TTS_MODE is 'real' but OPENAI_API_KEY is not set. "
                "Set OPENAI_API_KEY or change TTS_MODE to 'fake'."
            )
        tts_provider = OpenAITTSProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE,
            response_format=settings.TTS_RESPONSE_FORMAT,
            speed=settings.TTS_SPEED,
            timeout_seconds=settings.TTS_TIMEOUT_SECONDS,
        )
    else:
        tts_provider = FakeTTSProvider()

    tts_storage = AudioStorage()
    app.state.tts_service = TTSService(provider=tts_provider, storage=tts_storage, config=tts_config)
    app.state.tts_provider = tts_provider
    logger.info("TTS service initialized (mode=%s)", settings.TTS_MODE)

    yield

    # Cleanup
    if hasattr(app.state, "tts_provider") and app.state.tts_provider:
        await app.state.tts_provider.close()
    app.state.tts_service = None
    app.state.tts_provider = None
    _rag_service = None


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url="/redoc" if settings.ENV == "development" else None,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(checkin_router, prefix=settings.API_PREFIX)
app.include_router(sleep_log_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(routine_router, prefix=settings.API_PREFIX)
app.include_router(audio_router, prefix=settings.API_PREFIX)

# Mount only the audio subdirectory for static files
_audio_static_dir = Path(__file__).resolve().parent.parent / "static" / "audio"
_audio_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=str(_audio_static_dir)), name="audio-static")
