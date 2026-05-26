"""Global exception handler middleware."""
from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and maps them to JSON error responses."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        try:
            return await call_next(request)  # type: ignore[return-value]
        except ValueError as exc:
            logger.warning("validation_error", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={"detail": str(exc), "error": "BAD_REQUEST"},
            )
        except PermissionError as exc:
            logger.warning("permission_error", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": str(exc), "error": "FORBIDDEN"},
            )
        except LookupError as exc:
            logger.info("not_found_or_conflict", error=str(exc), path=request.url.path)
            return JSONResponse(
                status_code=409,
                content={"detail": str(exc), "error": "CONFLICT_OR_NOT_FOUND"},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "unhandled_exception", error=str(exc), path=request.url.path
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An unexpected error occurred",
                    "error": "INTERNAL_SERVER_ERROR",
                },
            )
