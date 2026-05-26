"""FastAPI dependency injection wiring."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, AsyncGenerator
from uuid import UUID

import httpx
import structlog
from fastapi import Depends, Header, HTTPException, Request
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class CurrentUser:
    """Decoded JWT claims for the authenticated user."""

    user_id: UUID
    email: str
    role: str


# ---------------------------------------------------------------------------
# DB Sessions
# ---------------------------------------------------------------------------


async def get_write_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async write session from the primary engine."""
    write_factory = request.app.state.write_session_factory
    async with write_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async read session from the replica engine."""
    read_factory = request.app.state.read_session_factory
    async with read_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------


async def get_redis(request: Request) -> Redis:  # type: ignore[type-arg]
    """Return the shared Redis client from app state."""
    return request.app.state.redis  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_JWKS_CACHE: dict = {}  # type: ignore[type-arg]


async def _fetch_jwks(jwks_url: str) -> dict:  # type: ignore[type-arg]
    """Fetch JWKS from the auth service (cached in-process)."""
    if _JWKS_CACHE:
        return _JWKS_CACHE

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _JWKS_CACHE.update(response.json())
    return _JWKS_CACHE


async def get_current_user(request: Request) -> CurrentUser:
    """Decode and validate a Bearer JWT; return the current user.

    Raises:
        HTTPException 401: if the token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ").strip()
    jwks_url: str = request.app.state.settings.jwt_public_key_url

    try:
        jwks = await _fetch_jwks(jwks_url)
        # Get the unverified header to find the key id
        unverified_header = jwt.get_unverified_header(token)
        # Find the matching key
        token_kid = unverified_header.get("kid")
        rsa_key: dict = {}  # type: ignore[type-arg]
        jwks_keys = jwks.get("keys", [])
        for key in jwks_keys:
            key_kid = key.get("kid")
            # Only match on kid if both token and key have one
            if token_kid and key_kid and token_kid == key_kid:
                rsa_key = {k: v for k, v in key.items() if k in ("kty","kid","use","n","e","alg")}
                break

        if not rsa_key:
            # No kid in token — use first key directly
            if jwks_keys:
                rsa_key = {k: v for k, v in jwks_keys[0].items() if k in ("kty","kid","use","n","e","alg")}

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        user_id = UUID(payload["sub"])
        email = str(payload.get("email", ""))
        role = str(payload.get("role", "USER"))
        return CurrentUser(user_id=user_id, email=email, role=role)

    except (JWTError, KeyError, ValueError) as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Dependency that enforces ADMIN role.

    Raises:
        HTTPException 403: if the user is not an admin.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def verify_internal_secret(
    request: Request,
    x_internal_secret: Annotated[str | None, Header()] = None,
) -> None:
    """Verify the shared internal service secret header.

    Raises:
        HTTPException 401: if the secret is missing or incorrect.
    """
    expected: str = request.app.state.settings.internal_service_secret
    if not x_internal_secret or x_internal_secret != expected:
        raise HTTPException(
            status_code=401, detail="Invalid or missing internal service secret"
        )
