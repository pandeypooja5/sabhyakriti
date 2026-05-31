"""FastAPI dependency injection — sessions, auth, and service wiring."""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

import httpx
import structlog
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from application.clients.product_service_client import ProductServiceClient
from application.services.cart_application_service import CartApplicationService
from application.services.coupon_application_service import CouponApplicationService
from infrastructure.persistence.database import get_async_session
from infrastructure.persistence.repositories.sqlalchemy_cart_repository import (
    SQLAlchemyCartRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_coupon_repository import (
    SQLAlchamyCouponRepository,
)
from infrastructure.persistence.repositories.sqlalchemy_wishlist_repository import (
    SQLAlchemyWishlistRepository,
)

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Security schemes
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)

# Module-level JWKS cache — populated lazily on first auth request
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch JWKS from the auth service (cached in-process)."""
    global _jwks_cache
    if _jwks_cache is None:
        url = os.environ.get("JWT_PUBLIC_KEY_URL", "")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWT_PUBLIC_KEY_URL not configured.",
            )
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


# ---------------------------------------------------------------------------
# DB session dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:  # type: ignore[return]
    """Yield an async DB session for the duration of a request."""
    async for session in get_async_session():
        yield session


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> dict:
    """Validate RS256 JWT and return the decoded claims.

    Raises:
        HTTPException 401: missing or invalid token
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        keys = jwks.get("keys", [])
        key_data = next((k for k in keys if k.get("kid") == kid), None)
        if key_data is None:
            # No kid in token — use first available key
            key_data = keys[0] if keys else None
        if key_data is None:
            raise JWTError("No matching key found in JWKS")

        public_key = jwk.construct(key_data)
        payload: dict = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_admin(
    claims: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Enforce admin role.

    Raises:
        HTTPException 403: if user does not have admin role
    """
    roles: list[str] = claims.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return claims


async def verify_internal_secret(
    x_internal_secret: Annotated[str | None, Header(alias="X-Internal-Secret")] = None,
) -> None:
    """Validate shared-secret header for internal service-to-service calls.

    Raises:
        HTTPException 401: missing or incorrect secret
    """
    expected = os.environ.get("INTERNAL_SERVICE_SECRET", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal secret not configured.",
        )
    if x_internal_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service secret.",
        )


# ---------------------------------------------------------------------------
# Service factory dependencies
# ---------------------------------------------------------------------------

def get_product_client() -> ProductServiceClient:
    """Return a ProductServiceClient configured from environment."""
    base_url = os.environ.get("PRODUCT_SERVICE_URL", "http://localhost:8001")
    internal_secret = os.environ.get("INTERNAL_SERVICE_SECRET", "")
    return ProductServiceClient(base_url=base_url, internal_secret=internal_secret)


async def get_cart_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    product_client: Annotated[ProductServiceClient, Depends(get_product_client)],
) -> CartApplicationService:
    """Build and return the CartApplicationService for a request."""
    return CartApplicationService(
        cart_repo=SQLAlchemyCartRepository(session),
        wishlist_repo=SQLAlchemyWishlistRepository(session),
        coupon_repo=SQLAlchamyCouponRepository(session),
        product_client=product_client,
    )


async def get_coupon_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CouponApplicationService:
    """Build and return the CouponApplicationService for a request."""
    return CouponApplicationService(
        coupon_repo=SQLAlchamyCouponRepository(session),
    )
