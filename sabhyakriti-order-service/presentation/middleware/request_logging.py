"""Structured request/response logging middleware."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every inbound request with duration and status code."""

    async def dispatch(
        self, request: Request, call_next: Callable[..., object]
    ) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        # Bind request context for all log lines produced during this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info("request_started")

        try:
            response: Response = await call_next(request)  # type: ignore[assignment]
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception("request_failed", duration_ms=round(duration_ms, 2))
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
