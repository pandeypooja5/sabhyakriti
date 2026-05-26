"""Middleware for structured request/response logging."""
from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and outgoing responses with timing."""

    def __init__(self, app: ASGIApp, service_name: str = "product-service") -> None:
        super().__init__(app)
        self._service_name = service_name

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            service=self._service_name,
        )

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_string=str(request.url.query),
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
