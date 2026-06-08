from __future__ import annotations

import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from application.services.aes_encryption_service import AESEncryptionService
from application.services.auth_application_service import AuthApplicationService
from application.services.jwt_service import JWTService
from application.services.totp_service import TOTPService
from infrastructure.adapters.aws_ses_adapter import AWSSESAdapter
from infrastructure.adapters.aws_secrets_adapter import get_secret
from infrastructure.adapters.facebook_oauth_adapter import FacebookOAuthAdapter
from infrastructure.adapters.google_oauth_adapter import GoogleOAuthAdapter
from infrastructure.adapters.hibp_adapter import HIBPAdapter
from infrastructure.adapters.twilio_sms_adapter import TwilioSMSAdapter
from infrastructure.adapters.twofactor_sms_adapter import TwoFactorSMSAdapter
from infrastructure.adapters.msg91_sms_adapter import MSG91SMSAdapter
from infrastructure.cache.redis_client import create_redis_client
from infrastructure.cache.redis_otp_repository import RedisOTPRepository
from infrastructure.cache.redis_replay_cache import RedisReplayCache
from infrastructure.cache.redis_token_repository import RedisTokenRepository
from infrastructure.persistence.database import create_engine, create_session_factory
from infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SQLAlchemyOAuthAccountRepository,
    SQLAlchemyUserRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_verification_repository import (
    SQLAlchemyEmailVerificationRepository,
    SQLAlchemyPasswordResetRepository,
)
from presentation.middleware.global_exception_handler import register_exception_handlers
from presentation.middleware.request_logging import RequestLoggingMiddleware
from presentation.middleware.security_headers import SecurityHeadersMiddleware
from presentation.routers.admin_auth_router import router as admin_auth_router
from presentation.routers.auth_router import router as auth_router
from presentation.routers.health_router import router as health_router
from presentation.routers.jwks_router import router as jwks_router
from presentation.routers.users_router import router as users_router


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    allowed_origins: str = "http://localhost:3000"

    # Database
    database_url: str  # e.g. postgresql+asyncpg://user:pass@host/db

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT — PEM or base64-encoded PEM (for Docker env vars); falls back to Secrets Manager
    jwt_private_key_pem: str = ""
    jwt_private_key_b64: str = ""  # base64-encoded PEM — convenience for local dev
    jwt_secrets_manager_key: str = ""

    # AES
    aes_key_b64: str = ""
    aes_secrets_manager_key: str = ""

    # AWS SES
    ses_from_address: str = "noreply@sabhyakriti.com"
    aws_region: str = "ap-south-1"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_secrets_manager_key: str = ""

    # 2Factor.in (India SMS OTP) — preferred when a real api key is set.
    # Delivery is gated on the key being present, independent of ENVIRONMENT.
    twofactor_api_key: str = ""
    twofactor_template_name: str = ""

    # MSG91 (India SMS OTP) — highest priority when configured. SMS-only route
    # (no voice fallback). Delivery gated on auth key + template id, not ENVIRONMENT.
    msg91_auth_key: str = ""
    msg91_template_id: str = ""
    msg91_sender_id: str = ""

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    facebook_client_id: str = ""
    facebook_client_secret: str = ""
    # Public site origin (HTTPS) used for OAuth redirect URIs + SPA bounce-back.
    public_base_url: str = "https://www.sabhyakriti.com"


# ── Logging ───────────────────────────────────────────────────────────────────

def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    _configure_logging()
    log = structlog.get_logger()

    settings = Settings()  # type: ignore[call-arg]
    app.state.settings = settings

    # ── Secrets ───────────────────────────────────────────────────────────────
    jwt_private_key_pem = settings.jwt_private_key_pem
    if not jwt_private_key_pem and settings.jwt_private_key_b64:
        import base64 as _b64
        jwt_private_key_pem = _b64.b64decode(settings.jwt_private_key_b64).decode()
    if not jwt_private_key_pem and settings.jwt_secrets_manager_key:
        jwt_private_key_pem = get_secret(settings.jwt_secrets_manager_key, settings.aws_region)

    aes_key_b64 = settings.aes_key_b64
    if not aes_key_b64 and settings.aes_secrets_manager_key:
        aes_key_b64 = get_secret(settings.aes_secrets_manager_key, settings.aws_region)

    twilio_account_sid = settings.twilio_account_sid
    twilio_auth_token = settings.twilio_auth_token
    if not twilio_account_sid and settings.twilio_secrets_manager_key:
        secret_json = get_secret(settings.twilio_secrets_manager_key, settings.aws_region)
        twilio_creds: dict = json.loads(secret_json)
        twilio_account_sid = twilio_creds["account_sid"]
        twilio_auth_token = twilio_creds["auth_token"]

    # ── Database ──────────────────────────────────────────────────────────────
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis = create_redis_client(settings.redis_url)
    app.state.redis = redis

    # ── Repositories ──────────────────────────────────────────────────────────
    user_repo = SQLAlchemyUserRepository(session_factory)
    oauth_repo = SQLAlchemyOAuthAccountRepository(session_factory)
    token_repo = RedisTokenRepository(redis)
    otp_repo = RedisOTPRepository(redis)
    email_verify_repo = SQLAlchemyEmailVerificationRepository(session_factory)
    password_reset_repo = SQLAlchemyPasswordResetRepository(session_factory)

    app.state.user_repo = user_repo
    app.state.email_verify_repo = email_verify_repo

    # ── Services ──────────────────────────────────────────────────────────────
    jwt_service = JWTService(jwt_private_key_pem)
    aes_service = AESEncryptionService(aes_key_b64)
    totp_service = TOTPService()
    app.state.jwt_service = jwt_service

    # ── External adapters ─────────────────────────────────────────────────────
    hibp_adapter = HIBPAdapter()
    # SMS provider priority (all send real SMS regardless of ENVIRONMENT):
    #   1. MSG91   — SMS-only OTP route (no voice fallback)
    #   2. 2Factor — India OTP
    #   3. Twilio  — fallback; only logs the OTP in development
    if settings.msg91_auth_key and not settings.msg91_auth_key.lower().startswith("dummy") and settings.msg91_template_id:
        sms_adapter = MSG91SMSAdapter(
            auth_key=settings.msg91_auth_key,
            template_id=settings.msg91_template_id,
            sender_id=settings.msg91_sender_id,
        )
        log.info("sms_provider_selected", provider="msg91")
    elif settings.twofactor_api_key and not settings.twofactor_api_key.lower().startswith("dummy"):
        sms_adapter = TwoFactorSMSAdapter(
            api_key=settings.twofactor_api_key,
            template_name=settings.twofactor_template_name,
        )
        log.info("sms_provider_selected", provider="2factor")
    else:
        sms_adapter = TwilioSMSAdapter(
            account_sid=twilio_account_sid,
            auth_token=twilio_auth_token,
            from_number=settings.twilio_from_number,
        )
        log.info("sms_provider_selected", provider="twilio")
    email_adapter = AWSSESAdapter(
        from_address=settings.ses_from_address,
        region=settings.aws_region,
    )
    app.state.email_adapter = email_adapter
    app.state.google_adapter = GoogleOAuthAdapter(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    app.state.facebook_adapter = FacebookOAuthAdapter(
        client_id=settings.facebook_client_id,
        client_secret=settings.facebook_client_secret,
    )

    replay_cache = RedisReplayCache(redis)

    # ── Application service ───────────────────────────────────────────────────
    auth_service = AuthApplicationService(
        user_repo=user_repo,
        oauth_repo=oauth_repo,
        token_repo=token_repo,
        otp_repo=otp_repo,
        email_verify_repo=email_verify_repo,
        password_reset_repo=password_reset_repo,
        jwt_service=jwt_service,
        aes_service=aes_service,
        totp_service=totp_service,
        hibp_adapter=hibp_adapter,
        sms_adapter=sms_adapter,
        email_adapter=email_adapter,
        replay_cache=replay_cache,
        frontend_origin=settings.frontend_origin,
    )
    app.state.auth_service = auth_service
    app.state.frontend_origin = settings.frontend_origin

    log.info("startup_complete", environment=settings.environment)
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await hibp_adapter.aclose()
    await redis.aclose()
    await engine.dispose()
    log.info("shutdown_complete")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = Settings()  # type: ignore[call-arg]

    app = FastAPI(
        title="Sabhyakriti Auth Service",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # CORS
    @app.middleware("http")
    async def _strip_trailing_slash(request, call_next):  # type: ignore[no-untyped-def]
        _p = request.scope.get("path", "")
        if len(_p) > 1 and _p.endswith("/"):
            request.scope["path"] = _p.rstrip("/")
            request.scope["raw_path"] = request.scope["path"].encode()
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Exception handlers (must be registered before routers)
    register_exception_handlers(app)

    # Routers
    app.include_router(health_router)
    app.include_router(jwks_router)
    app.include_router(auth_router)
    app.include_router(admin_auth_router)
    app.include_router(users_router)

    return app


app = create_app()
