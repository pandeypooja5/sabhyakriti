"""Structured request/response logging middleware."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming HTTP request and outgoing response with duration.

    Attaches a per-request trace_id that can be forwarded to downstream
    services for distributed tracing.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        start = time.monotonic()

        # Bind trace context for all log statements within this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info(
            "request_started",
            query_params=str(request.query_params),
        )

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Trace-Id"] = trace_id
        return response
