"""Middleware that emits a structured log line for every HTTP request."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging with correlation ID."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:  # type: ignore[type-arg]
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        log = logger.bind(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )
        log.info("request_started")

        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log.info(
            "request_finished",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response
