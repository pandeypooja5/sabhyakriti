"""
FastAPI dependency injection providers.

Provides:
- DB sessions (read / write)
- JWT-authenticated current user
- Admin guard
- Internal-secret guard
- Application service instances
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.clients.notification_service_client import NotificationServiceClient
from application.clients.payment_service_client import PaymentServiceClient
from application.clients.product_service_client import ProductServiceClient
from application.services.address_application_service import AddressApplicationService
from application.services.invoice_service import InvoiceService
from application.services.order_application_service import OrderApplicationService
from config import Settings, get_settings
from infrastructure.persistence.repositories.sqlalchemy_address_repository import (
    SQLAlchemyAddressRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_order_repository import (
    SQLAlchemyOrderRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_return_repository import (
    SQLAlchemyReturnRepository,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Database session providers
# ---------------------------------------------------------------------------


async def get_write_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async write (primary) DB session."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.write_session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async read (replica) DB session."""
    factory: async_sessionmaker[AsyncSession] = request.app.state.read_session_factory
    async with factory() as session:
        yield session


# ---------------------------------------------------------------------------
# JWT authentication
# ---------------------------------------------------------------------------


class CurrentUser:
    """Parsed JWT claims for the authenticated user."""

    def __init__(self, user_id: str, roles: list[str]) -> None:
        self.user_id = user_id
        self.roles = roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


_jwks_cache: dict[str, object] = {}


async def _fetch_jwks(jwks_url: str) -> dict[str, object]:
    global _jwks_cache  # noqa: PLW0603
    if _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Validate Bearer JWT and return parsed user claims."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ")

    try:
        jwks = await _fetch_jwks(settings.jwt_public_key_url)
        keys = jwks.get("keys", [])
        key = keys[0] if keys else jwks
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub", "")
        roles: list[str] = payload.get("roles", [])
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
            )
        return CurrentUser(user_id=user_id, roles=roles)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Guard: reject non-admin users with 403."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def verify_internal_secret(
    request: Request,
    x_internal_secret: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    """Guard: verify X-Internal-Secret header for internal endpoints."""
    if x_internal_secret != settings.internal_service_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal secret",
        )


# ---------------------------------------------------------------------------
# Application service providers
# ---------------------------------------------------------------------------


def get_order_service(
    request: Request,
    write_session: Annotated[AsyncSession, Depends(get_write_db)],
    read_session: Annotated[AsyncSession, Depends(get_read_db)],
) -> OrderApplicationService:
    order_repo = SQLAlchemyOrderRepository(
        write_session=write_session,
        read_session=read_session,
    )
    return_repo = SQLAlchemyReturnRepository(session=write_session)

    return OrderApplicationService(
        order_repo=order_repo,
        return_repo=return_repo,
        product_client=request.app.state.product_client,
        payment_client=request.app.state.payment_client,
        notification_client=request.app.state.notification_client,
    )


def get_address_service(
    write_session: Annotated[AsyncSession, Depends(get_write_db)],
) -> AddressApplicationService:
    return AddressApplicationService(
        address_repo=SQLAlchemyAddressRepository(session=write_session)
    )


def get_invoice_service(
    settings: Settings = Depends(get_settings),
) -> InvoiceService:
    return InvoiceService(
        seller_gstin=settings.seller_gstin,
        seller_address=settings.seller_address,
    )
