"""Sabhyakriti Product Service — FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis

from application.clients.order_service_client import OrderServiceClient
from application.services.category_application_service import CategoryApplicationService
from application.services.product_application_service import ProductApplicationService
from application.services.review_application_service import ReviewApplicationService
from infrastructure.adapters.aws_s3_adapter import AWSS3Adapter
from infrastructure.cache.plp_cache_repository import PlpCacheRepository
from infrastructure.persistence.database import create_engines, create_session_factories
from infrastructure.persistence.repositories.sqlalchemy_category_repository import (
    SQLAlchemyCategoryRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_image_repository import (
    SQLAlchemyImageRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_review_repository import (
    SQLAlchemyReviewRepository,
)
from presentation.middleware.global_exception_handler import (
    GlobalExceptionHandlerMiddleware,
)
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers import (
    bulk_upload_router,
    category_router,
    health_router,
    internal_router,
    product_router,
    review_router,
)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_primary_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sabhyakriti"
    database_replica_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sabhyakriti"
    redis_url: str = "redis://localhost:6379/1"
    aws_region: str = "ap-south-1"
    s3_bucket_name: str = "sabhyakriti-product-images"
    cloudfront_domain: str = "localhost"
    order_service_internal_url: str = "http://localhost:8001"
    internal_service_secret: str = "dev-secret"
    jwt_public_key_url: str = "http://localhost:8000/internal/v1/auth/jwks.json"
    frontend_origin: str = "http://localhost:3000"
    log_level: str = "INFO"
    app_env: str = "development"
    app_port: int = 8002


# ---------------------------------------------------------------------------
# Structlog configuration
# ---------------------------------------------------------------------------


def configure_logging(log_level: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


# ---------------------------------------------------------------------------
# Service factory helpers (stored on app.state, called per-request by routers)
# ---------------------------------------------------------------------------


class ServiceFactory:
    """Builds request-scoped application services using stored session factories."""

    def __init__(
        self,
        settings: Settings,
        write_factory,  # type: ignore[no-untyped-def]
        read_factory,  # type: ignore[no-untyped-def]
        redis: Redis,  # type: ignore[type-arg]
        s3_adapter: AWSS3Adapter,
        order_client: OrderServiceClient,
    ) -> None:
        self._settings = settings
        self._write_factory = write_factory
        self._read_factory = read_factory
        self._redis = redis
        self._s3 = s3_adapter
        self._order_client = order_client
        self._plp_cache = PlpCacheRepository(redis)

    def build_product_service(
        self,
        write_session,  # type: ignore[no-untyped-def]
        read_session,  # type: ignore[no-untyped-def]
    ) -> ProductApplicationService:
        product_repo = SQLAlchemyProductRepository(write_session, read_session)
        category_repo = SQLAlchemyCategoryRepository(write_session, read_session)
        image_repo = SQLAlchemyImageRepository(write_session, read_session)
        review_repo = SQLAlchemyReviewRepository(write_session, read_session)
        return ProductApplicationService(
            product_repo=product_repo,
            category_repo=category_repo,
            image_repo=image_repo,
            review_repo=review_repo,
            plp_cache=self._plp_cache,
            s3_adapter=self._s3,
            cloudfront_domain=self._settings.cloudfront_domain,
            s3_bucket=self._settings.s3_bucket_name,
        )

    def build_review_service(
        self,
        write_session,  # type: ignore[no-untyped-def]
        read_session,  # type: ignore[no-untyped-def]
    ) -> ReviewApplicationService:
        review_repo = SQLAlchemyReviewRepository(write_session, read_session)
        return ReviewApplicationService(
            review_repo=review_repo,
            order_client=self._order_client,
        )

    def build_category_service(
        self,
        write_session,  # type: ignore[no-untyped-def]
        read_session,  # type: ignore[no-untyped-def]
    ) -> CategoryApplicationService:
        category_repo = SQLAlchemyCategoryRepository(write_session, read_session)
        return CategoryApplicationService(category_repo=category_repo)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings: Settings = app.state.settings

    configure_logging(settings.log_level)
    logger = structlog.get_logger(__name__)
    logger.info("starting_up", env=settings.app_env)

    # Create DB engines
    primary_engine, replica_engine = create_engines(
        primary_url=settings.database_primary_url,
        replica_url=settings.database_replica_url,
        echo=(settings.app_env == "development"),
    )
    write_factory, read_factory = create_session_factories(primary_engine, replica_engine)
    app.state.write_session_factory = write_factory
    app.state.read_session_factory = read_factory

    # Redis (DB 1)
    redis: Redis = Redis.from_url(  # type: ignore[type-arg]
        settings.redis_url, decode_responses=True
    )
    app.state.redis = redis

    # AWS adapters
    s3_adapter = AWSS3Adapter(
        bucket_name=settings.s3_bucket_name,
        region=settings.aws_region,
    )

    # Order service client
    order_client = OrderServiceClient(
        base_url=settings.order_service_internal_url,
        internal_secret=settings.internal_service_secret,
    )

    # Service factory
    svc_factory = ServiceFactory(
        settings=settings,
        write_factory=write_factory,
        read_factory=read_factory,
        redis=redis,
        s3_adapter=s3_adapter,
        order_client=order_client,
    )
    app.state.service_factory = svc_factory

    logger.info("startup_complete", port=settings.app_port)
    yield

    # Shutdown
    logger.info("shutting_down")
    await redis.aclose()
    await order_client.close()
    await primary_engine.dispose()
    await replica_engine.dispose()
    logger.info("shutdown_complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = Settings()

    app = FastAPI(
        title="Sabhyakriti Product Service",
        description=(
            "Product catalogue microservice for the Sabhyakriti Saree eCommerce platform"
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )
    app.state.settings = settings

    # Middleware (outermost first)
    app.add_middleware(GlobalExceptionHandlerMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware, service_name="product-service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router.router)
    app.include_router(product_router.router)
    app.include_router(category_router.router)
    app.include_router(review_router.router)
    app.include_router(internal_router.router)
    app.include_router(bulk_upload_router.router)

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    _settings = Settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=_settings.app_port,
        reload=_settings.app_env == "development",
        workers=1 if _settings.app_env == "development" else 4,
    )
