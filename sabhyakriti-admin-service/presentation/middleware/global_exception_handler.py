"""Global exception handler middleware — ensures no raw 5xx leaks to admin UI."""

from __future__ import annotations

import traceback
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catch any unhandled exception and return a safe JSON error envelope."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except ValueError as exc:
            logger.warning("validation_error", detail=str(exc))
            return JSONResponse(
                status_code=422,
                content={"detail": str(exc)},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "unhandled_exception",
                error=str(exc),
                traceback=traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "An unexpected error occurred. Please try again later."},
            )
