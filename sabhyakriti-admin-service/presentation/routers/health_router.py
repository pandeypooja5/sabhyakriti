"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/health", response_model=HealthResponse, include_in_schema=True)
async def health_check() -> HealthResponse:
    """Liveness probe — returns 200 if the process is running."""
    return HealthResponse(status="ok", service="sabhyakriti-admin-service")
