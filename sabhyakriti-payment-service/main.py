"""Application entry point for sabhyakriti-payment-service.

Startup sequence:
  1. Load settings from environment
  2. Load Razorpay credentials from AWS Secrets Manager
  3. Initialise async DB engine
  4. Wire APScheduler (auto-cancel job every 5 minutes)
  5. Mount middleware and routers

Port: 8005
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.adapters.aws_secrets_adapter import AWSSecretsAdapter
from infrastructure.adapters.razorpay_adapter import RazorpayAdapter
from infrastructure.persistence.database import close_db, init_db
from presentation.middleware.global_exception_handler import GlobalExceptionHandlerMiddleware
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers.health_router import router as health_router
from presentation.routers.internal_router import router as internal_router
from presentation.routers.payment_router import router as payment_router

# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(os.getenv("LOG_LEVEL", "INFO"))
    ),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle hook."""
    # ---- Startup ----
    logger.info("payment_service_starting")

    # 1. Load configuration from environment
    database_url = os.environ["DATABASE_URL"]
    order_service_url = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8001")
    notification_service_url = os.environ.get(
        "NOTIFICATION_SERVICE_URL", "http://localhost:8006"
    )
    internal_service_secret = os.environ.get("INTERNAL_SERVICE_SECRET", "")
    aws_region = os.environ.get("AWS_REGION", "ap-south-1")
    key_id_secret = os.environ.get(
        "SECRETS_MANAGER_RAZORPAY_KEY_ID", "sabhyakriti/payment/razorpay_key_id"
    )
    key_secret_secret = os.environ.get(
        "SECRETS_MANAGER_RAZORPAY_KEY_SECRET", "sabhyakriti/payment/razorpay_key_secret"
    )
    webhook_secret_secret = os.environ.get(
        "SECRETS_MANAGER_RAZORPAY_WEBHOOK_SECRET",
        "sabhyakriti/payment/razorpay_webhook_secret",
    )

    # 2. Load Razorpay credentials from AWS Secrets Manager
    #    Fall back to environment variables in development / test
    app_env = os.environ.get("APP_ENV", "development")
    if app_env == "production":
        secrets_adapter = AWSSecretsAdapter(region_name=aws_region)
        razorpay_secrets = await secrets_adapter.load_razorpay_secrets(
            key_id_secret, key_secret_secret, webhook_secret_secret
        )
        razorpay_key_id = razorpay_secrets.key_id
        razorpay_key_secret = razorpay_secrets.key_secret
        razorpay_webhook_secret = razorpay_secrets.webhook_secret
    else:
        # Development / CI: read directly from environment
        razorpay_key_id = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_key_id")
        razorpay_key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "rzp_test_key_secret")
        razorpay_webhook_secret = os.environ.get(
            "RAZORPAY_WEBHOOK_SECRET", "rzp_test_webhook_secret"
        )

    # 3. Initialise database
    init_db(database_url)
    logger.info("database_initialised")

    # 4. Create Razorpay adapter
    razorpay_adapter = RazorpayAdapter(razorpay_key_id, razorpay_key_secret)

    # 5. Store shared state on app
    app.state.order_service_url = order_service_url
    app.state.notification_service_url = notification_service_url
    app.state.internal_service_secret = internal_service_secret
    app.state.razorpay_adapter = razorpay_adapter
    app.state.razorpay_key_id = razorpay_key_id
    app.state.razorpay_key_secret = razorpay_key_secret
    app.state.razorpay_webhook_secret = razorpay_webhook_secret

    # 6. Start APScheduler for auto-cancel job
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _cancel_stale_payments_job,
        "interval",
        minutes=5,
        id="cancel_stale_payments",
        args=[app],
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("scheduler_started")

    logger.info("payment_service_ready", port=int(os.getenv("PORT", 8000)))
    yield

    # ---- Shutdown ----
    logger.info("payment_service_stopping")
    scheduler.shutdown(wait=False)
    await close_db()
    logger.info("payment_service_stopped")


async def _cancel_stale_payments_job(app: FastAPI) -> None:
    """APScheduler job: cancel CREATED payments older than 30 minutes.

    Creates its own DB session so it runs independently of any HTTP request.
    """
    from infrastructure.persistence.database import get_async_session
    from infrastructure.persistence.repositories.sqlalchemy_payment_repository import (
        SQLAlchemyPaymentRepository,
    )
    from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
        SQLAlchemyWebhookRepository,
    )
    from application.clients.notification_service_client import NotificationServiceClient
    from application.clients.order_service_client import OrderServiceClient
    from application.services.payment_application_service import PaymentApplicationService

    try:
        async for session in get_async_session():
            payment_repo = SQLAlchemyPaymentRepository(session)
            webhook_repo = SQLAlchemyWebhookRepository(session)
            order_client = OrderServiceClient(
                base_url=app.state.order_service_url,
                internal_secret=app.state.internal_service_secret,
            )
            notification_client = NotificationServiceClient(
                base_url=app.state.notification_service_url,
                internal_secret=app.state.internal_service_secret,
            )
            service = PaymentApplicationService(
                payment_repo=payment_repo,
                webhook_repo=webhook_repo,
                razorpay_adapter=app.state.razorpay_adapter,
                order_client=order_client,
                notification_client=notification_client,
                razorpay_key_id=app.state.razorpay_key_id,
                razorpay_key_secret=app.state.razorpay_key_secret,
                razorpay_webhook_secret=app.state.razorpay_webhook_secret,
            )
            count = await service.cancel_stale_payments()
            if count > 0:
                logger.info("auto_cancel_job_completed", cancelled=count)
    except Exception as exc:  # noqa: BLE001
        logger.error("auto_cancel_job_failed", error=str(exc))


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

    application = FastAPI(
        title="Sabhyakriti Payment Service",
        version="0.1.0",
        description="Payment microservice for the Sabhyakriti Saree eCommerce platform.",
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # --- Middleware (outermost first) ---
    @application.middleware("http")
    async def _strip_trailing_slash(request, call_next):  # type: ignore[no-untyped-def]
        _p = request.scope.get("path", "")
        if len(_p) > 1 and _p.endswith("/"):
            request.scope["path"] = _p.rstrip("/")
            request.scope["raw_path"] = request.scope["path"].encode()
        return await call_next(request)

    application.add_middleware(GlobalExceptionHandlerMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    )

    # --- Routers ---
    application.include_router(health_router)
    application.include_router(payment_router)
    application.include_router(internal_router)

    return application


app = create_app()
