"""Health checks and Kubernetes-style probes."""

import time

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import APP_NAME, APP_VERSION, HealthResponse

router = APIRouter(tags=["Monitoring"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check (Legacy)",
    description="Returns basic health status for backward compatibility.",
)
def get_health() -> HealthResponse:
    """Return application operational health."""
    return HealthResponse(
        status="healthy",
        app=APP_NAME,
        version=APP_VERSION,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Kubernetes Liveness Probe",
    description="Verifies the Python ASGI application process is responsive.",
)
def get_liveness():
    """Liveness probe: verifies process responsiveness without external dependencies."""
    return {
        "status": "alive",
        "app": APP_NAME,
        "timestamp": time.time(),
    }


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Kubernetes Readiness Probe",
    description="Verifies application readiness and active database connectivity.",
)
def get_readiness(response: Response, db: Session = Depends(get_db)):
    """Readiness probe: validates connectivity to required database backend."""
    try:
        # Bounded query to verify database is answering
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "app": APP_NAME,
            "database": "connected",
            "timestamp": time.time(),
        }
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "app": APP_NAME,
            "database": "disconnected",
            "error": "Database connectivity check failed",
            "timestamp": time.time(),
        }
