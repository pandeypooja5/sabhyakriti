"""Structured request/response logging middleware using structlog."""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every inbound request and outbound response with timing.

    Adds a unique request_id to each log entry for tracing.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            client=request.client.host if request.client else "unknown",
        )

        response: Response = await call_next(request)  # type: ignore[arg-type]

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
