"""Application entry point for sabhyakriti-cart-service.

Startup sequence (lifespan):
  1. Load secrets from AWS Secrets Manager (if SECRET_NAME set)
  2. Initialise async DB engine and session factory
  3. Wire middleware: security headers, request logging, exception handler
  4. Mount all routers

Port: 8003
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.adapters.aws_secrets_adapter import load_secrets_to_env
from infrastructure.persistence.database import close_db, init_db
from presentation.middleware.global_exception_handler import (
    GlobalExceptionHandlerMiddleware,
)
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers import (
    cart_router,
    coupon_router,
    health_router,
    internal_router,
    wishlist_router,
)

# ---------------------------------------------------------------------------
# Configure structlog
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle handler."""
    logger.info("cart_service_starting", port=int(os.getenv("PORT", 8000)))

    # 1. Load secrets
    load_secrets_to_env()

    # 2. Initialise database
    init_db()
    logger.info("database_initialised")

    yield

    # Shutdown
    await close_db()
    logger.info("cart_service_stopped")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Sabhyakriti Cart Service",
    description="Shopping cart, wishlist, and coupon management for Sabhyakriti Saree eCommerce.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware (order matters — outermost = first to run on request)
# ---------------------------------------------------------------------------

app.add_middleware(GlobalExceptionHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router.router)
app.include_router(cart_router.router)
app.include_router(wishlist_router.router)
app.include_router(coupon_router.router)
app.include_router(internal_router.router)
