"""Global exception handler middleware.

Maps domain exceptions to appropriate HTTP status codes.
"""

from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and maps them to JSON error responses.

    Mapping:
        ValueError      → 400 Bad Request
        PermissionError → 403 Forbidden
        LookupError     → 404 Not Found
        Exception       → 500 Internal Server Error
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> JSONResponse:
        try:
            response = await call_next(request)  # type: ignore[arg-type]
            return response  # type: ignore[return-value]
        except ValueError as exc:
            logger.warning("bad_request", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc)},
            )
        except PermissionError as exc:
            logger.warning("forbidden", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": str(exc)},
            )
        except LookupError as exc:
            logger.info("not_found", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=404,
                content={"detail": str(exc)},
            )
        except Exception as exc:
            logger.error(
                "unhandled_exception",
                error=str(exc),
                path=request.url.path,
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred."},
            )
