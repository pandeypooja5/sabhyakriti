from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    db_status = "ok"
    redis_status = "ok"
    http_status = status.HTTP_200_OK

    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        await request.app.state.redis.ping()
    except Exception:
        redis_status = "error"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={"status": "ok" if http_status == 200 else "degraded", "db": db_status, "redis": redis_status},
    )
