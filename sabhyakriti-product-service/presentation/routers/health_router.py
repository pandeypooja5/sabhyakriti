"""Health check endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict:  # type: ignore[type-arg]
    """Returns 200 OK if the service is running."""
    return {"status": "ok", "service": "sabhyakriti-product-service"}


@router.get("/health/ready", summary="Readiness probe")
async def readiness(request: Request) -> dict:  # type: ignore[type-arg]
    """Checks DB and Redis connectivity."""
    checks: dict = {}  # type: ignore[type-arg]

    # Check primary DB
    try:
        write_factory = request.app.state.write_session_factory
        async with write_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    # Check Redis
    try:
        redis = request.app.state.redis
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }
