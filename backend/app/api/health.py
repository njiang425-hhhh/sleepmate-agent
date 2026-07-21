from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "sleepmate-agent"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe — verifies database and critical services are reachable."""
    from app.core.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        return {"status": "not_ready", "database": "unavailable"}

    return {"status": "ready"}
