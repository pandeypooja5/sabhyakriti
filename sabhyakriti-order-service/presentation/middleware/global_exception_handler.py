"""Global exception handler middleware."""

from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


async def value_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map ValueError to 400 Bad Request."""
    logger.warning("validation_error", detail=str(exc))
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


async def permission_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map PermissionError to 403 Forbidden."""
    logger.warning("permission_denied", detail=str(exc))
    return JSONResponse(
        status_code=403,
        content={"detail": "You do not have permission to perform this action"},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all 500 handler — never leak internal details."""
    logger.exception("unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )
