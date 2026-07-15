import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
                __import__("pathlib").Path(__file__).resolve().parent.parent / settings.CHROMA_PERSIST_DIR
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

    yield

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
