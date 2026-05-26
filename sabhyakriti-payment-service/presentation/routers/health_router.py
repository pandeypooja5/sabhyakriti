"""Health check endpoints — used by load balancers and container orchestrators."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse, include_in_schema=False)
async def health() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    return HealthResponse(status="ok", service="sabhyakriti-payment-service")


@router.get("/health/ready", response_model=HealthResponse, include_in_schema=False)
async def readiness() -> HealthResponse:
    """Readiness probe — returns 200 when the service is ready to accept traffic."""
    return HealthResponse(status="ready", service="sabhyakriti-payment-service")
