"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe — returns 200 when the process is running."""
    return HealthResponse(
        status="ok",
        service="sabhyakriti-order-service",
        version="1.0.0",
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check(request: Request) -> HealthResponse:
    """
    Readiness probe — verifies DB connectivity before reporting ready.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    write_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.write_session_factory
    )
    try:
        async with write_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database not reachable")

    return HealthResponse(
        status="ready",
        service="sabhyakriti-order-service",
        version="1.0.0",
    )
