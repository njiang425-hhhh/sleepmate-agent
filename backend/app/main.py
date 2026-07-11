from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.checkin import router as checkin_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.sleep_log import router as sleep_log_router
from app.core.config import settings
from app.core.database import engine, Base
from app.models.sleep_log import SleepLog  # noqa: F401 — ensure model is registered

app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url="/redoc" if settings.ENV == "development" else None,
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


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
