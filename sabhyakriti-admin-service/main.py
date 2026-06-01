"""sabhyakriti-admin-service — application entry point."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.clients.auth_service_client import AuthServiceClient
from application.clients.cart_service_client import CartServiceClient
from application.clients.order_service_client import OrderServiceClient
from application.clients.product_service_client import ProductServiceClient
from application.services.admin_application_service import AdminApplicationService
from presentation.middleware.global_exception_handler import GlobalExceptionHandlerMiddleware
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers import customer_router, dashboard_router, health_router, proxy_router

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
        if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        structlog.stdlib.NAME_TO_LEVEL.get(
            os.getenv("LOG_LEVEL", "INFO").upper(), 20
        )
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable '{name}' is not set")
    return value


async def _fetch_jwt_public_key(jwks_url: str, http_client: httpx.AsyncClient) -> str:
    """Fetch the RS256 public key (PEM) from the Auth Service JWKS endpoint."""
    try:
        response = await http_client.get(jwks_url, timeout=10.0)
        response.raise_for_status()
        # Expect the Auth Service to expose the PEM directly or wrapped in JSON
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            # Support {"public_key": "-----BEGIN..."} or first key in JWKS keys array
            if "public_key" in data:
                key: str = data["public_key"]
                return key
            # Standard JWKS: return first key as JSON string for jose
            keys = data.get("keys", [])
            if keys and "pem" in keys[0]:
                pem: str = keys[0]["pem"]
                return pem
            if keys:
                import json as _json
                return _json.dumps(keys[0])
        return response.text  # assume raw PEM
    except httpx.HTTPError as exc:
        logger.warning(
            "jwt_public_key_fetch_failed",
            url=jwks_url,
            error=str(exc),
        )
        # Return a placeholder — token validation will fail at runtime
        return ""


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup; tear down on shutdown."""
    order_service_url = _require_env("ORDER_SERVICE_URL")
    product_service_url = _require_env("PRODUCT_SERVICE_URL")
    auth_service_url = _require_env("AUTH_SERVICE_URL")
    cart_service_url = _require_env("CART_SERVICE_URL")
    internal_secret = _require_env("INTERNAL_SERVICE_SECRET")
    jwt_public_key_url = _require_env("JWT_PUBLIC_KEY_URL")

    # Shared httpx client — connection pooling across all downstream calls
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        follow_redirects=False,
    )

    # Fetch JWT public key at startup
    jwt_public_key = await _fetch_jwt_public_key(jwt_public_key_url, http_client)
    if not jwt_public_key:
        logger.warning("jwt_public_key_empty — authentication will fail for all requests")

    # Instantiate service clients
    order_client = OrderServiceClient(order_service_url, internal_secret, http_client)
    product_client = ProductServiceClient(product_service_url, internal_secret, http_client)
    auth_client = AuthServiceClient(auth_service_url, internal_secret, http_client)
    cart_client = CartServiceClient(cart_service_url, internal_secret, http_client)

    # Instantiate application service
    admin_service = AdminApplicationService(order_client, product_client, auth_client)

    # Attach to app state for dependency injection
    app.state.jwt_public_key = jwt_public_key
    app.state.admin_service = admin_service
    app.state.product_client = product_client
    app.state.order_client = order_client
    app.state.cart_client = cart_client

    logger.info("admin_service.started", port=int(os.getenv("PORT", 8000)))

    yield  # application runs here

    # Cleanup
    await http_client.aclose()
    logger.info("admin_service.stopped")


# ---------------------------------------------------------------------------
# FastAPI application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    application = FastAPI(
        title="Sabhyakriti Admin Service",
        description="Admin BFF — pure aggregation layer for the Sabhyakriti platform.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS — only allow admin frontend origin
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware stack (outermost = first to run)
    application.add_middleware(GlobalExceptionHandlerMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)

    # Routers
    application.include_router(health_router.router)
    application.include_router(dashboard_router.router)
    application.include_router(customer_router.router)
    application.include_router(proxy_router.router)

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
        workers=1,  # single worker in dev; Dockerfile uses 2
    )
