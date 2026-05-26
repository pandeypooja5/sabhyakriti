"""Global exception handler middleware — turns unhandled exceptions into 500 JSON."""

from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler registered on the FastAPI app.

    Logs the full traceback to structlog (CloudWatch) and returns a generic
    500 response so internal details are never leaked to callers.
    """
    logger.error(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )
