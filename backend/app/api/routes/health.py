"""Health check endpoints for monitoring system status."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/liveness")
def liveness() -> dict:
    """
    Simple liveness check.

    Returns:
        dict: Status indicating the service is alive
    """
    return {"status": "ok"}


@router.get("/readiness")
def readiness(db: Session = Depends(get_db)) -> JSONResponse:
    """
    Check all dependencies and return readiness status.

    This endpoint checks:
    - Database connectivity
    - Redis connectivity (if configured)
    - LLM API availability (basic check)

    Args:
        db: Database session dependency

    Returns:
        JSONResponse: Status and individual component checks
    """
    checks = {}

    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Redis check
    try:
        from app.core.queue import redis_client

        redis_client.ping()
        checks["redis"] = "ok"
    except ImportError:
        checks["redis"] = "not configured"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    # LLM API check (lightweight - just check if settings exist)
    try:
        from app.core.settings import get_settings

        settings = get_settings()
        if settings.config.llm.base_url:
            checks["llm"] = "ok"
        else:
            checks["llm"] = "not configured"
    except Exception as e:
        checks["llm"] = f"error: {str(e)}"

    # Determine overall status
    all_ok = all(v == "ok" or v == "not configured" for v in checks.values())
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
        },
    )
