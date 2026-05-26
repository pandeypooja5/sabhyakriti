"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 OK when the service is running.",
)
async def health_check() -> HealthResponse:
    """Simple liveness probe — no DB check needed for load-balancer pings."""
    return HealthResponse(
        status="ok",
        service="sabhyakriti-notification-service",
        version="1.0.0",
    )


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Returns 200 OK when the service is ready to handle requests.",
)
async def readiness_check() -> HealthResponse:
    """Readiness probe — same as liveness for now; extend with DB ping if needed."""
    return HealthResponse(
        status="ready",
        service="sabhyakriti-notification-service",
        version="1.0.0",
    )
