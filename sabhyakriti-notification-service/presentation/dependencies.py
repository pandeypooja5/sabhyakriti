"""
FastAPI dependency injection providers.

Provides:
- get_db:                     async DB session
- verify_internal_secret:     X-Internal-Secret header guard
- get_notification_service:   fully wired NotificationApplicationService
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.notification_application_service import NotificationApplicationService
from infrastructure.persistence.database import get_db_session
from infrastructure.persistence.repositories.sqlalchemy_notification_log_repository import (
    SQLAlchemyNotificationLogRepository,
)

logger = structlog.get_logger(__name__)


# ── Database session ───────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a scoped async DB session."""
    async for session in get_db_session():
        yield session


# ── Internal secret guard ──────────────────────────────────────────────────────

async def verify_internal_secret(
    request: Request,
    x_internal_secret: Annotated[str | None, Header()] = None,
) -> None:
    """
    Dependency that validates the X-Internal-Secret header.

    Raises HTTP 401 if the header is missing or does not match the configured
    secret.  This is the only auth mechanism for internal-only endpoints.
    """
    expected: str = request.app.state.internal_secret
    if not x_internal_secret or x_internal_secret != expected:
        logger.warning(
            "internal_secret_mismatch",
            path=request.url.path,
            provided_secret_prefix=(x_internal_secret or "")[:4] or "MISSING",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Internal-Secret header.",
        )


# ── Notification service ───────────────────────────────────────────────────────

async def get_notification_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationApplicationService:
    """Build and return a request-scoped NotificationApplicationService."""
    log_repo = SQLAlchemyNotificationLogRepository(session=session)
    return NotificationApplicationService(
        jinja_env=request.app.state.jinja_env,
        ses_adapter=request.app.state.ses_adapter,
        twilio_adapter=request.app.state.twilio_adapter,
        sns_adapter=request.app.state.sns_adapter,
        log_repo=log_repo,
    )
