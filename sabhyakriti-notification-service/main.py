"""
sabhyakriti-notification-service entry point.

Lifespan:
  startup  — read env/secrets, init DB engine, init Jinja2, wire adapters
  shutdown — dispose DB connections

The application runs on port 8006 (internal-only; not exposed via public ALB).
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader, select_autoescape

from infrastructure.adapters.aws_ses_adapter import AWSSESAdapter
from infrastructure.adapters.aws_sns_adapter import AWSSNSAdapter
from infrastructure.adapters.twilio_sms_adapter import TwilioSMSAdapter
from infrastructure.persistence.database import close_db, init_db
from presentation.middleware.global_exception_handler import global_exception_handler
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers.health_router import router as health_router
from presentation.routers.notification_router import router as notification_router

# ── Configure structured logging ───────────────────────────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}.get(
            os.getenv("LOG_LEVEL", "INFO").upper(), 20
        )
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup on startup, teardown on shutdown."""
    logger.info("notification_service_starting")

    # ── Database ───────────────────────────────────────────────────────────────
    database_url = os.environ["DATABASE_URL"]
    init_db(database_url)
    logger.info("database_engine_initialised")

    # ── Jinja2 template environment ────────────────────────────────────────────
    templates_dir = Path(__file__).parent / "templates"
    jinja_env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
        enable_async=False,  # rendering is CPU-bound; sync is fine in executor
    )
    app.state.jinja_env = jinja_env
    logger.info("jinja2_environment_initialised", templates_dir=str(templates_dir))

    # ── AWS SES adapter ────────────────────────────────────────────────────────
    app.state.ses_adapter = AWSSESAdapter(
        region=os.environ.get("AWS_REGION", "ap-south-1"),
        from_email=os.environ.get("SES_FROM_EMAIL", "no-reply@sabhyakriti.com"),
        from_name=os.environ.get("SES_FROM_NAME", "Sabhyakriti"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    logger.info("ses_adapter_initialised")

    # ── Twilio SMS adapter ─────────────────────────────────────────────────────
    app.state.twilio_adapter = TwilioSMSAdapter(
        account_sid=os.environ["TWILIO_ACCOUNT_SID"],
        auth_token=os.environ["TWILIO_AUTH_TOKEN"],
        from_number=os.environ["TWILIO_FROM_NUMBER"],
    )
    logger.info("twilio_adapter_initialised")

    # ── AWS SNS adapter (SMS fallback) ─────────────────────────────────────────
    app.state.sns_adapter = AWSSNSAdapter(
        region=os.environ.get("SNS_SMS_REGION", "ap-south-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    logger.info("sns_adapter_initialised")

    # ── Internal secret ────────────────────────────────────────────────────────
    internal_secret = os.environ["INTERNAL_SERVICE_SECRET"]
    if internal_secret == "change-me-to-a-long-random-secret":
        logger.warning("internal_secret_is_default_value_change_in_production")
    app.state.internal_secret = internal_secret

    logger.info("notification_service_started", port=int(os.getenv("PORT", 8000)))

    yield  # ── Application is running ──────────────────────────────────────────

    # ── Teardown ───────────────────────────────────────────────────────────────
    await close_db()
    logger.info("notification_service_stopped")


# ── FastAPI application ────────────────────────────────────────────────────────

app = FastAPI(
    title="Sabhyakriti Notification Service",
    description=(
        "Internal microservice for sending transactional email (via AWS SES) "
        "and SMS (via Twilio with SNS fallback) notifications. "
        "All endpoints are internal-only and protected by X-Internal-Secret header."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware (applied in reverse registration order) ─────────────────────────
@app.middleware("http")
async def _strip_trailing_slash(request, call_next):  # type: ignore[no-untyped-def]
    _p = request.scope.get("path", "")
    if len(_p) > 1 and _p.endswith("/"):
        request.scope["path"] = _p.rstrip("/")
        request.scope["raw_path"] = request.scope["path"].encode()
    return await call_next(request)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# ── Exception handlers ─────────────────────────────────────────────────────────
app.add_exception_handler(Exception, global_exception_handler)  # type: ignore[arg-type]

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(notification_router)
