"""Global exception handler middleware.

Catches unhandled exceptions and converts them to consistent JSON error
responses without leaking internal stack traces to clients.
"""

from __future__ import annotations

from collections.abc import Callable

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catch-all exception handler that returns RFC 7807 Problem Details."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:  # type: ignore[type-arg]
        try:
            return await call_next(request)  # type: ignore[return-value]
        except ValueError as exc:
            logger.warning("client_error", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc)},
            )
        except PermissionError as exc:
            logger.warning("forbidden", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied."},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "unhandled_exception",
                error=str(exc),
                path=request.url.path,
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal error occurred."},
            )
