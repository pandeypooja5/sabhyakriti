"""FastAPI dependency injection providers.

All ``Depends``-compatible callables live here so that router modules stay
thin and the wiring is easy to swap in tests.
"""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from application.clients.notification_service_client import NotificationServiceClient
from application.clients.order_service_client import OrderServiceClient
from application.services.payment_application_service import PaymentApplicationService
from infrastructure.persistence.database import get_async_session
from infrastructure.persistence.repositories.sqlalchemy_payment_repository import (
    SQLAlchemyPaymentRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SQLAlchemyWebhookRepository,
)

logger = structlog.get_logger(__name__)

_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session for the duration of one request."""
    async for session in get_async_session():
        yield session


# ---------------------------------------------------------------------------
# JWT authentication
# ---------------------------------------------------------------------------


class TokenPayload:
    """Minimal decoded JWT payload."""

    def __init__(self, user_id: UUID, email: str, roles: list[str]) -> None:
        self.user_id = user_id
        self.email = email
        self.roles = roles


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> TokenPayload:
    """Decode and validate the Bearer JWT from the Authorization header.

    The public key URL is fetched from ``JWT_PUBLIC_KEY_URL`` env var.
    For simplicity we decode with algorithm HS256 here; in production swap
    to RS256 and fetch the JWKS from ``JWT_PUBLIC_KEY_URL``.
    """
    token = credentials.credentials
    jwks_url = os.getenv("JWT_PUBLIC_KEY_URL", "")

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient() as _c:
            resp = await _c.get(jwks_url, timeout=5)
            jwks = resp.json()
        keys = jwks.get("keys", [])
        key = keys[0] if keys else jwks
        payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
        user_id = UUID(payload["sub"])
        email = payload.get("email", "")
        roles = payload.get("roles", [payload.get("role", "")])
        return TokenPayload(user_id=user_id, email=email, roles=roles)
    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("jwt_decode_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_admin(
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
) -> TokenPayload:
    """Dependency that requires the caller to have the ``admin`` role."""
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Internal secret
# ---------------------------------------------------------------------------


def verify_internal_secret(
    x_internal_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Validate the ``X-Internal-Secret`` header for service-to-service calls."""
    expected = os.getenv("INTERNAL_SERVICE_SECRET", "")
    if not expected or x_internal_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal service secret.",
        )


# ---------------------------------------------------------------------------
# Application service factory
# ---------------------------------------------------------------------------


def get_payment_service(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentApplicationService:
    """Construct a ``PaymentApplicationService`` for a single request.

    Razorpay credentials and client instances are resolved from app state
    (set in the lifespan handler in ``main.py``).
    """
    state = request.app.state

    payment_repo = SQLAlchemyPaymentRepository(db)
    webhook_repo = SQLAlchemyWebhookRepository(db)

    order_client = OrderServiceClient(
        base_url=state.order_service_url,
        internal_secret=state.internal_service_secret,
    )
    notification_client = NotificationServiceClient(
        base_url=state.notification_service_url,
        internal_secret=state.internal_service_secret,
    )

    return PaymentApplicationService(
        payment_repo=payment_repo,
        webhook_repo=webhook_repo,
        razorpay_adapter=state.razorpay_adapter,
        order_client=order_client,
        notification_client=notification_client,
        razorpay_key_id=state.razorpay_key_id,
        razorpay_key_secret=state.razorpay_key_secret,
        razorpay_webhook_secret=state.razorpay_webhook_secret,
    )
