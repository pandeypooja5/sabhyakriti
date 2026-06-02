"""
sabhyakriti-order-service entry point.

Configures:
- Structured logging (structlog + stdlib)
- Lifespan: engine creation, session factories, HTTP clients
- Middleware: security headers, request logging
- Exception handlers: ValueError (400), PermissionError (403), generic (500)
- All routers: customer, admin, address, internal, health
- CORS
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from application.clients.notification_service_client import NotificationServiceClient
from application.clients.payment_service_client import PaymentServiceClient
from application.clients.product_service_client import ProductServiceClient
from infrastructure.persistence.database import create_engines, create_session_factories
from presentation.middleware.global_exception_handler import (
    generic_exception_handler,
    permission_error_handler,
    value_error_handler,
)
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers.address_router import router as address_router
from presentation.routers.admin_order_router import router as admin_router
from presentation.routers.health_router import router as health_router
from presentation.routers.internal_router import router as internal_router, admin_router as internal_admin_router
from presentation.routers.order_router import router as order_router


def _configure_logging(log_level: str) -> None:
    """Set up structlog with consistent JSON output."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level.upper())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialise resources on startup, dispose on shutdown."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    logger = structlog.get_logger(__name__)
    logger.info("order_service_starting", port=settings.app_port)

    # Create dual DB engines and session factories
    primary_engine, replica_engine = create_engines(settings)
    write_factory, read_factory = create_session_factories(primary_engine, replica_engine)

    app.state.primary_engine = primary_engine
    app.state.replica_engine = replica_engine
    app.state.write_session_factory = write_factory
    app.state.read_session_factory = read_factory

    # Initialise service HTTP clients
    app.state.product_client = ProductServiceClient(
        base_url=settings.product_service_url,
        internal_secret=settings.internal_service_secret,
    )
    app.state.payment_client = PaymentServiceClient(
        base_url=settings.payment_service_url,
        internal_secret=settings.internal_service_secret,
    )
    app.state.notification_client = NotificationServiceClient(
        base_url=settings.notification_service_url,
        internal_secret=settings.internal_service_secret,
    )

    logger.info("order_service_ready")
    yield

    # Cleanup
    await primary_engine.dispose()
    await replica_engine.dispose()
    logger.info("order_service_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Sabhyakriti Order Service",
        description="Order management microservice for Sabhyakriti Saree eCommerce",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    @app.middleware("http")
    async def _strip_trailing_slash(request, call_next):  # type: ignore[no-untyped-def]
        _p = request.scope.get("path", "")
        if len(_p) > 1 and _p.endswith("/"):
            request.scope["path"] = _p.rstrip("/")
            request.scope["raw_path"] = request.scope["path"].encode()
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # ------------------------------------------------------------------ #
    # Custom middleware (applied in LIFO order)                            #
    # ------------------------------------------------------------------ #
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # ------------------------------------------------------------------ #
    # Exception handlers                                                   #
    # ------------------------------------------------------------------ #
    app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(PermissionError, permission_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)

    # ------------------------------------------------------------------ #
    # Routers                                                              #
    # ------------------------------------------------------------------ #
    app.include_router(health_router)
    app.include_router(order_router)
    app.include_router(admin_router)
    app.include_router(address_router)
    app.include_router(internal_router)
    app.include_router(internal_admin_router)

    return app


app = create_app()
