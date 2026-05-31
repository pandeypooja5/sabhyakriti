"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Annotated, Any

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from application.services.admin_application_service import AdminApplicationService

logger = structlog.get_logger(__name__)

_bearer = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _get_jwt_public_key(request: Request) -> str:
    """Pull the cached RS256 public key from app state."""
    key: str = request.app.state.jwt_public_key
    return key


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict[str, Any]:
    """Validate the Bearer JWT using the RS256 public key.

    Returns the decoded payload dict on success.
    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    public_key_raw = _get_jwt_public_key(request)
    token = credentials.credentials

    try:
        import json as _json
        try:
            key: Any = _json.loads(public_key_raw) if public_key_raw.startswith("{") else public_key_raw
        except Exception:
            key = public_key_raw
        payload: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def require_admin(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    """Raise HTTP 403 if the authenticated user does not have the ADMIN role.

    Supports both 'role' (singular string, e.g. 'ADMIN') and 'roles' (list)
    JWT claim formats emitted by the auth service.
    """
    roles: list[str] = current_user.get("roles", [])
    role_str: str = current_user.get("role", "")
    if "ADMIN" not in roles and role_str.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


# ---------------------------------------------------------------------------
# Service dependency
# ---------------------------------------------------------------------------

def get_admin_service(request: Request) -> AdminApplicationService:
    """Return the singleton AdminApplicationService from app state."""
    service: AdminApplicationService = request.app.state.admin_service
    return service


# ---------------------------------------------------------------------------
# Proxy header helper
# ---------------------------------------------------------------------------

def forward_headers(request: Request) -> dict[str, str]:
    """Extract the Authorization header from the incoming admin request
    so it can be forwarded verbatim to downstream services."""
    auth_header = request.headers.get("Authorization", "")
    headers: dict[str, str] = {}
    if auth_header:
        headers["Authorization"] = auth_header
    return headers
